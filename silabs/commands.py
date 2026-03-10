"""
Command definitions for Silabs CLI
"""

import click
from pathlib import Path
from .config import Config
from .tools import ToolManager
from .utils import (
    run_command, find_project_root, validate_project,
    print_error, print_warning, print_success, get_build_dir,
    load_slcp_file, save_slcp_file, load_slcc_file, backup_file
)


@click.group()
@click.version_option()
@click.option("-C", "--project-dir", type=click.Path(), help="Project directory")
@click.option("-B", "--build-dir", type=click.Path(), help="Build directory")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.pass_context
def silabs(ctx, project_dir, build_dir, verbose):
    """Silabs CLI - Command-line interface for Simplicity Studio 6"""
    ctx.ensure_object(dict)
    
    # Initialize config and tools
    config = Config()
    tool_manager = ToolManager(config)
    
    ctx.obj["config"] = config
    ctx.obj["tool_manager"] = tool_manager
    ctx.obj["verbose"] = verbose
    
    # Find project root
    project_root = Path(project_dir) if project_dir else find_project_root()
    
    if project_root and validate_project(project_root):
        ctx.obj["project_root"] = project_root
        ctx.obj["build_dir"] = get_build_dir(
            project_root,
            Path(build_dir) if build_dir else None
        )
    else:
        ctx.obj["project_root"] = None
        ctx.obj["build_dir"] = None


@silabs.command()
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
def version(ctx, verbose):
    """Show tool versions"""
    tool_manager = ctx.obj["tool_manager"]
    
    if verbose:
        tool_manager.print_tool_status()
    else:
        print("Silabs CLI v0.1.0")


@silabs.command()
@click.pass_context
def build(ctx):
    """Build the project"""
    if not ctx.obj["project_root"]:
        print_error("Not in a Silabs project directory")
        return
    
    project_root = ctx.obj["project_root"]
    build_dir = ctx.obj["build_dir"]
    tool_manager = ctx.obj["tool_manager"]
    verbose = ctx.obj["verbose"]
    
    print_success(f"Building {project_root.name}")
    
    env = tool_manager.get_environment()
    cmd = f"cd {build_dir} && cmake {project_root} && ninja"
    
    exit_code, stdout, stderr = run_command(
        cmd,
        env=env,
        verbose=verbose,
        capture_output=False
    )
    
    if exit_code != 0:
        print_error(f"Build failed with exit code {exit_code}")
        if stderr:
            print(stderr)


@silabs.command()
@click.pass_context
def clean(ctx):
    """Remove build output"""
    if not ctx.obj["project_root"]:
        print_error("Not in a Silabs project directory")
        return
    
    build_dir = ctx.obj["build_dir"]
    
    if (build_dir / "build.ninja").exists() or (build_dir / "CMakeCache.txt").exists():
        cmd = f"cd {build_dir} && ninja clean"
        exit_code, _, _ = run_command(cmd, verbose=ctx.obj["verbose"])
        
        if exit_code == 0:
            print_success("Clean completed")
        else:
            print_warning("Clean may have failed partially")


@silabs.command()
@click.pass_context
def fullclean(ctx):
    """Delete entire build directory"""
    if not ctx.obj["project_root"]:
        print_error("Not in a Silabs project directory")
        return
    
    build_dir = ctx.obj["build_dir"]
    
    if build_dir.exists():
        import shutil
        try:
            shutil.rmtree(build_dir)
            print_success(f"Removed {build_dir}")
        except Exception as e:
            print_error(f"Failed to remove build directory: {e}")


@silabs.command()
@click.pass_context
def reconfigure(ctx):
    """Force CMake reconfiguration"""
    if not ctx.obj["project_root"]:
        print_error("Not in a Silabs project directory")
        return
    
    project_root = ctx.obj["project_root"]
    build_dir = ctx.obj["build_dir"]
    tool_manager = ctx.obj["tool_manager"]
    verbose = ctx.obj["verbose"]
    
    print_success("Reconfiguring project...")
    
    # Remove CMake cache files to force reconfiguration
    cache_files = [
        build_dir / "CMakeCache.txt",
        build_dir / "CMakeFiles",
    ]
    
    for cache_file in cache_files:
        if cache_file.exists():
            if cache_file.is_file():
                cache_file.unlink()
            else:
                import shutil
                shutil.rmtree(cache_file)
    
    # Run CMake configuration
    env = tool_manager.get_environment()
    cmd = f"cd {build_dir} && cmake {project_root}"
    
    exit_code, stdout, stderr = run_command(
        cmd,
        env=env,
        verbose=verbose,
        capture_output=False
    )
    
    if exit_code != 0:
        print_error(f"Reconfiguration failed with exit code {exit_code}")
        if stderr:
            print(stderr)
    else:
        print_success("Reconfiguration completed")


@silabs.command()
@click.argument("what", required=False, default="app")
@click.option("--port", help="Serial port for flashing")
@click.option("--baud", default=115200, help="Baud rate for flashing")
@click.pass_context
def flash(ctx, what, port, baud):
    """Flash firmware to device"""
    if not ctx.obj["project_root"]:
        print_error("Not in a Silabs project directory")
        return
    
    build_dir = ctx.obj["build_dir"]
    tool_manager = ctx.obj["tool_manager"]
    
    # Find the binary to flash
    binary_path = None
    if what == "app":
        # Look for .hex or .bin files in build directory
        for ext in [".hex", ".bin"]:
            candidates = list(build_dir.glob(f"**/*{ext}"))
            if candidates:
                binary_path = candidates[0]  # Take first match
                break
    
    if not binary_path:
        print_error(f"Could not find {what} binary to flash")
        return
    
    print_success(f"Flashing {what}: {binary_path}")
    
    # Use Commander tool for flashing
    commander_path = tool_manager.get_tool_path("commander")
    if not commander_path:
        print_error("Commander tool not found")
        return
    
    env = tool_manager.get_environment()
    
    # Commander flash command
    cmd = f"{commander_path} flash {binary_path}"
    if port:
        cmd += f" --serialno {port}"
    
    exit_code, stdout, stderr = run_command(
        cmd,
        env=env,
        verbose=ctx.obj["verbose"],
        capture_output=False
    )
    
    if exit_code != 0:
        print_error(f"Flash failed with exit code {exit_code}")
        if stderr:
            print(stderr)
    else:
        print_success("Flash completed successfully")


@silabs.command()
@click.option("--port", help="Serial port for monitor")
@click.option("--baud", default=115200, help="Baud rate for monitor")
@click.pass_context
def monitor(ctx, port, baud):
    """Start serial monitor"""
    tool_manager = ctx.obj["tool_manager"]
    
    # For now, use a simple approach - could be enhanced with proper serial monitoring
    print_success("Starting serial monitor...")
    print(f"Port: {port or 'auto-detect'}")
    print(f"Baud: {baud}")
    
    # This is a placeholder - real implementation would use serial library
    # For now, just show that the command is recognized
    print_warning("Monitor functionality requires additional serial library integration")
    print("Use: pip install pyserial")


@silabs.command()
@click.option("--port", help="Serial port for erase")
@click.pass_context
def erase(ctx, port):
    """Erase device flash"""
    tool_manager = ctx.obj["tool_manager"]
    
    commander_path = tool_manager.get_tool_path("commander")
    if not commander_path:
        print_error("Commander tool not found")
        return
    
    print_success("Erasing device flash...")
    
    env = tool_manager.get_environment()
    cmd = f"{commander_path} device masserase"
    if port:
        cmd += f" --serialno {port}"
    
    exit_code, stdout, stderr = run_command(
        cmd,
        env=env,
        verbose=ctx.obj["verbose"],
        capture_output=False
    )
    
    if exit_code != 0:
        print_error(f"Erase failed with exit code {exit_code}")
        if stderr:
            print(stderr)
    else:
        print_success("Device erased successfully")


@silabs.command()
@click.pass_context
def size(ctx):
    """Show binary size information"""
    if not ctx.obj["project_root"]:
        print_error("Not in a Silabs project directory")
        return
    
    build_dir = ctx.obj["build_dir"]
    tool_manager = ctx.obj["tool_manager"]
    
    # Look for ELF file
    elf_files = list(build_dir.glob("**/*.elf"))
    if not elf_files:
        print_error("No ELF file found in build directory")
        return
    
    elf_path = elf_files[0]
    
    # Use GCC size utility
    gcc_path = tool_manager.get_tool_path("gcc-arm-none-eabi")
    if gcc_path:
        size_cmd = f"{gcc_path}/bin/arm-none-eabi-size"
    else:
        # Fallback to system size
        size_cmd = "size"
    
    env = tool_manager.get_environment()
    cmd = f"{size_cmd} {elf_path}"
    
    exit_code, stdout, stderr = run_command(
        cmd,
        env=env,
        verbose=False,
        capture_output=True
    )
    
    if exit_code == 0:
        print(f"Size information for {elf_path.name}:")
        print(stdout)
    else:
        print_error("Failed to get size information")
        if stderr:
            print(stderr)


@silabs.command()
@click.argument("topic", required=False)
@click.pass_context
def docs(ctx, topic):
    """Open documentation"""
    import webbrowser
    
    base_url = "https://docs.silabs.com/"
    
    if topic:
        # Try to find specific documentation
        if "getting-started" in topic.lower():
            url = f"{base_url}simplicity-studio-5-users-guide/1.0.0/ss-5-users-guide-getting-started/"
        elif "api" in topic.lower():
            url = f"{base_url}gecko-platform/4.0/"
        else:
            url = f"{base_url}search#q={topic}"
    else:
        # Open main documentation
        url = base_url
    
    print_success(f"Opening documentation: {url}")
    try:
        webbrowser.open(url)
    except Exception as e:
        print_error(f"Failed to open browser: {e}")
        print(f"Please visit: {url}")


@silabs.group()
@click.pass_context
def component(ctx):
    """Manage project components"""
    pass


@component.command("list")
@click.option("--category", help="Filter by category")
@click.option("--available", is_flag=True, help="Show only available components")
@click.pass_context
def component_list(ctx, category, available):
    """List project components"""
    if not ctx.obj["project_root"]:
        print_error("Not in a Silabs project directory")
        return
    
    project_root = ctx.obj["project_root"]
    
    if available:
        # Show available components from slc-cli
        tool_manager = ctx.obj["tool_manager"]
        slc_path = tool_manager.get_tool_path("slc-cli")
        
        if not slc_path:
            print_error("slc-cli not found")
            return
        
        print_success("Listing available components...")
        
        # Use slc component list command
        cmd = [str(slc_path), "component", "list"]
        if category:
            cmd.extend(["--category", category])
        
        result = run_command(cmd, cwd=project_root)
        if result[0] != 0:
            print_error("Failed to list components")
            return
    else:
        # Show installed components from .slcp file
        slcp_config = load_slcp_file(project_root)
        if not slcp_config:
            print_error("Could not load project configuration")
            return
        
        print_success("Installed components:")
        
        # Look for components in the configuration
        components = slcp_config.get("component", [])
        if not components:
            print("  No components installed")
            return
        
        for comp in components:
            name = comp.get("name", "unknown")
            version = comp.get("version", "latest")
            print(f"  - {name} ({version})")


@component.command("install")
@click.argument("name")
@click.option("--version", help="Component version")
@click.pass_context
def component_install(ctx, name, version):
    """Install a component"""
    if not ctx.obj["project_root"]:
        print_error("Not in a Silabs project directory")
        return
    
    project_root = ctx.obj["project_root"]
    tool_manager = ctx.obj["tool_manager"]
    slc_path = tool_manager.get_tool_path("slc-cli")
    
    if not slc_path:
        print_error("slc-cli not found")
        return
    
    print_success(f"Installing component: {name}")
    
    # Load current configuration
    slcp_config = load_slcp_file(project_root)
    if not slcp_config:
        print_error("Could not load project configuration")
        return
    
    # Check if component is already installed
    components = slcp_config.get("component", [])
    for comp in components:
        if comp.get("name") == name:
            print_warning(f"Component {name} is already installed")
            return
    
    # Use slc-cli to install the component
    cmd = [str(slc_path), "component", "install", name]
    if version:
        cmd.extend(["--version", version])
    
    result = run_command(cmd, cwd=project_root)
    if result[0] != 0:
        print_error("Failed to install component")
        return
    
    # Add to .slcp file
    new_component = {"name": name}
    if version:
        new_component["version"] = version
    
    components.append(new_component)
    slcp_config["component"] = components
    
    if save_slcp_file(project_root, slcp_config):
        print_success(f"Component {name} installed successfully")
    else:
        print_error("Component installed but failed to update configuration")


@component.command("remove")
@click.argument("name")
@click.pass_context
def component_remove(ctx, name):
    """Remove a component"""
    if not ctx.obj["project_root"]:
        print_error("Not in a Silabs project directory")
        return
    
    project_root = ctx.obj["project_root"]
    tool_manager = ctx.obj["tool_manager"]
    slc_path = tool_manager.get_tool_path("slc-cli")
    
    if not slc_path:
        print_error("slc-cli not found")
        return
    
    print_success(f"Removing component: {name}")
    
    # Load current configuration
    slcp_config = load_slcp_file(project_root)
    if not slcp_config:
        print_error("Could not load project configuration")
        return
    
    # Check if component is installed
    components = slcp_config.get("component", [])
    component_found = False
    updated_components = []
    
    for comp in components:
        if comp.get("name") == name:
            component_found = True
        else:
            updated_components.append(comp)
    
    if not component_found:
        print_warning(f"Component {name} is not installed")
        return
    
    # Use slc-cli to remove the component
    cmd = [str(slc_path), "component", "remove", name]
    result = run_command(cmd, cwd=project_root)
    if result[0] != 0:
        print_error("Failed to remove component")
        return
    
    # Update .slcp file
    slcp_config["component"] = updated_components
    
    if save_slcp_file(project_root, slcp_config):
        print_success(f"Component {name} removed successfully")
    else:
        print_error("Component removed but failed to update configuration")


@component.command("info")
@click.argument("name")
@click.pass_context
def component_info(ctx, name):
    """Show component information"""
    if not ctx.obj["project_root"]:
        print_error("Not in a Silabs project directory")
        return
    
    project_root = ctx.obj["project_root"]
    
    # First check if component is installed in .slcp
    slcp_config = load_slcp_file(project_root)
    if slcp_config:
        components = slcp_config.get("component", [])
        installed_comp = None
        for comp in components:
            if comp.get("name") == name:
                installed_comp = comp
                break
        
        if installed_comp:
            print_success(f"Component: {name}")
            print(f"Version: {installed_comp.get('version', 'latest')}")
            print(f"Status: Installed")
        else:
            print_success(f"Component: {name}")
            print("Status: Not installed")
    
    # Try to find .slcc file for the component
    # Components are typically in the components directory
    components_dir = project_root / "components"
    if components_dir.exists():
        for comp_dir in components_dir.iterdir():
            if comp_dir.is_dir() and comp_dir.name == name:
                slcc_config = load_slcc_file(comp_dir)
                if slcc_config:
                    print()
                    print("Component configuration:")
                    description = slcc_config.get("description", "No description")
                    print(f"Description: {description}")
                    
                    dependencies = slcc_config.get("dependencies", [])
                    if dependencies:
                        print("Dependencies:")
                        for dep in dependencies:
                            print(f"  - {dep}")
                    else:
                        print("Dependencies: None")
                break
    
    # If no .slcc file found, try slc-cli for info
    tool_manager = ctx.obj["tool_manager"]
    slc_path = tool_manager.get_tool_path("slc-cli")
    
    if slc_path:
        print()
        print("Querying slc-cli for additional information...")
        cmd = [str(slc_path), "component", "info", name]
        result = run_command(cmd, cwd=project_root)
        if result[0] != 0:
            print_warning("Could not get additional component information from slc-cli")


@silabs.command()
@click.pass_context
def menuconfig(ctx):
    """Interactive component configuration"""
    if not ctx.obj["project_root"]:
        print_error("Not in a Silabs project directory")
        return
    
    project_root = ctx.obj["project_root"]
    
    # Load current .slcp configuration
    slcp_config = load_slcp_file(project_root)
    if not slcp_config:
        print_error("Could not load project configuration")
        return
    
    print_success("Current project configuration:")
    print(f"Project: {slcp_config.get('project', {}).get('name', 'Unknown')}")
    print(f"Target: {slcp_config.get('project', {}).get('device', 'Unknown')}")
    
    components = slcp_config.get("component", [])
    if components:
        print(f"Components ({len(components)}):")
        for comp in components:
            name = comp.get("name", "unknown")
            version = comp.get("version", "latest")
            print(f"  - {name} ({version})")
    else:
        print("Components: None")
    
    print()
    print("To modify configuration, use:")
    print("  - silabs component install/remove <name>")
    print("  - Or edit the .slcp file directly")
    print("  - Or use Simplicity Studio for advanced configuration")
    
    # For advanced configuration, suggest using slc-cli
    tool_manager = ctx.obj["tool_manager"]
    slc_path = tool_manager.get_tool_path("slc-cli")
    
    if slc_path:
        print()
        print("For advanced configuration, you can also use:")
        print(f"  {slc_path} configuration --edit")


@silabs.command()
@click.pass_context
def config(ctx):
    """Show project configuration"""
    config = ctx.obj["config"]
    
    if config.config_path:
        print(f"Config file: {config.config_path}")
        print()
        
        for section, values in config.data.items():
            print(f"[{section}]")
            for key, value in values.items():
                if isinstance(value, list):
                    print(f"  {key} = [")
                    for item in value:
                        print(f"    {item}")
                    print("  ]")
                else:
                    print(f"  {key} = {value}")
            print()
    else:
        print_warning("No config file found")


@silabs.command()
@click.pass_context
def tools(ctx):
    """Show tool status"""
    tool_manager = ctx.obj["tool_manager"]
    tool_manager.print_tool_status()


@silabs.command()
@click.argument("name")
@click.option("--template", default="basic", help="Project template (basic, empty)")
@click.option("--target", help="Target device/board")
@click.pass_context
def create_project(ctx, name, template, target):
    """Create a new Silabs project"""
    import shutil
    
    project_dir = Path.cwd() / name
    
    if project_dir.exists():
        print_error(f"Directory {name} already exists")
        return
    
    # Create project directory
    project_dir.mkdir(parents=True)
    
    # Create basic project structure
    (project_dir / "src").mkdir()
    (project_dir / "include").mkdir()
    (project_dir / "config").mkdir()
    
    # Create main.c
    main_c = f'''#include "sl_iostream.h"
#include "sl_iostream_init_instances.h"

int main(void)
{{
    // Initialize Silicon Labs device, system, board, and application
    sl_system_init();

    // Initialize the console
    sl_iostream_init_instances();

    sl_iostream_printf(SL_IOSTREAM_STDOUT, "Hello World!\\n");

    while (1) {{
        // Application code here
        sl_iostream_printf(SL_IOSTREAM_STDOUT, "Running...\\n");
        sl_sleeptimer_delay_millisecond(1000);
    }}
}}
'''
    
    with open(project_dir / "src" / "main.c", "w") as f:
        f.write(main_c)
    
    # Create CMakeLists.txt
    cmake_lists = f'''cmake_minimum_required(VERSION 3.16.3)
project({name})

# Add executable
add_executable(${{PROJECT_NAME}}
    src/main.c
)

# Link libraries
target_link_libraries(${{PROJECT_NAME}}
    # Add your libraries here
)

# Include directories
target_include_directories(${{PROJECT_NAME}} PUBLIC
    include
)
'''
    
    with open(project_dir / "CMakeLists.txt", "w") as f:
        f.write(cmake_lists)
    
    # Create .slconf file
    config = ctx.obj["config"]
    project_config = {
        "project": {
            "name": name,
            "template": template,
        },
        "slc": {
            "sdk-package-path": config.get("slc", "sdk-package-path", []),
        },
        "toolchain": {
            "gcc-arm-none-eabi": config.get("toolchain", "gcc-arm-none-eabi", ""),
        }
    }
    
    if target:
        project_config["project"]["target"] = target
    
    # Save project config
    project_config_path = project_dir / "project.slconf"
    import toml
    with open(project_config_path, "w") as f:
        toml.dump(project_config, f)
    
    print_success(f"Created project '{name}' in {project_dir}")
    print(f"Template: {template}")
    if target:
        print(f"Target: {target}")
    print()
    print("Next steps:")
    print(f"  cd {name}")
    print("  silabs set-target <target>" if not target else "  silabs build")


@silabs.command()
@click.pass_context
def list_projects(ctx):
    """List Silabs projects in current directory"""
    from pathlib import Path
    
    projects = []
    for item in Path.cwd().iterdir():
        if item.is_dir() and (item / "project.slconf").exists():
            projects.append(item.name)
    
    if not projects:
        print("No Silabs projects found in current directory")
        return
    
    print("Silabs Projects:")
    print("-" * 40)
    for project in sorted(projects):
        print(f"  {project}")


@silabs.command()
@click.argument("target")
@click.pass_context
def set_target(ctx, target):
    """Set the target device/board for the project"""
    if not ctx.obj["project_root"]:
        print_error("Not in a Silabs project directory")
        return
    
    project_root = ctx.obj["project_root"]
    config_path = project_root / "project.slconf"
    
    if not config_path.exists():
        print_error("Project config file not found")
        return
    
    # Load current config
    import toml
    with open(config_path) as f:
        config_data = toml.load(f)
    
    # Update target
    if "project" not in config_data:
        config_data["project"] = {{}}
    config_data["project"]["target"] = target
    
    # Save config
    with open(config_path, "w") as f:
        toml.dump(config_data, f)
    
    print_success(f"Set target to {target}")


@silabs.command()
@click.pass_context
def list_targets(ctx):
    """List available targets/devices"""
    tool_manager = ctx.obj["tool_manager"]
    
    # For now, show some common targets
    # TODO: Query slc-cli for actual available targets
    targets = [
        "EFR32BG22C224F512IM40",  # xG22
        "EFR32BG24B220F1024IM40", # xG24
        "EFR32MG12P332F1024GL125", # Mighty Gecko
        "EFR32FG12P233F1024GL125", # Flex Gecko
    ]
    
    print("Available Targets:")
    print("-" * 40)
    for target in targets:
        print(f"  {target}")
    
    print()
    print("Note: This is a static list. Full target discovery requires slc-cli.")


@silabs.command()
@click.pass_context
def info(ctx):
    """Show project information"""
    if not ctx.obj["project_root"]:
        print_warning("Not in a Silabs project directory")
        return
    
    project_root = ctx.obj["project_root"]
    build_dir = ctx.obj["build_dir"]
    config = ctx.obj["config"]
    
    print(f"Project: {project_root.name}")
    print(f"Root: {project_root}")
    print(f"Build: {build_dir}")
    print()
    
    # Load project config
    config_path = project_root / "project.slconf"
    if config_path.exists():
        import toml
        with open(config_path) as f:
            project_config = toml.load(f)
        
        if "project" in project_config:
            proj_info = project_config["project"]
            print("Project Config:")
            for key, value in proj_info.items():
                print(f"  {key}: {value}")
            print()
    
    ctx.invoke(tools)
