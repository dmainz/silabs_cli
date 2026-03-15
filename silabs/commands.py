"""
Command definitions for Silabs CLI
"""

import click
import curses
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import yaml
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


def _find_component_database() -> Optional[str]:
    """Find component database file in common locations."""
    search_paths = [
        Path.cwd() / "components.json",
        Path.cwd() / "components.yaml",
        Path.home() / ".silabs" / "components.json",
        Path.home() / ".silabs" / "components.yaml",
    ]

    for path in search_paths:
        if path.exists():
            return str(path)
    return None


def _load_component_database(db_path: str) -> Optional[Dict[str, Any]]:
    """Load component database from file."""
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            if db_path.endswith('.json'):
                return json.load(f)
            elif db_path.endswith('.yaml') or db_path.endswith('.yml'):
                return yaml.safe_load(f)
    except Exception as e:
        print_warning(f"Failed to load component database: {e}")
    return None


def _list_components_by_category(components_data: Dict[str, Any], category: str):
    """List components in a specific category."""
    category_components = components_data.get('category_components', {})
    components = components_data.get('components', {})

    if category not in category_components:
        print_error(f"Category '{category}' not found")
        print("Available categories:")
        for cat in sorted(category_components.keys()):
            print(f"  {cat}")
        return

    comp_entries = category_components[category]
    print_success(f"Components in category '{category}' ({len(comp_entries)} found):")

    # Support both legacy (list of IDs) and new (list of dicts) formats
    for entry in comp_entries:
        if isinstance(entry, dict):
            comp_id = entry.get('id')
            location = entry.get('location')
        else:
            comp_id = entry
            location = None

        comp_info = components.get(comp_id, {})
        description = comp_info.get('description', 'No description')
        quality = comp_info.get('quality', 'unknown')

        print(f"  {comp_id} ({quality})")
        if description:
            print(f"    {description}")
        if location:
            print(f"    location: {location}")
        print()


def _list_all_components_from_db(components_data: Dict[str, Any]):
    """List all components from database."""
    components = components_data.get('components', {})
    categories = components_data.get('category_components', {})

    print_success(f"All available components ({len(components)} total):")

    # Group by category
    for category in sorted(categories.keys()):
        comp_entries = categories[category]
        if comp_entries:
            print(f"\n{category} ({len(comp_entries)} components):")
            for entry in comp_entries:
                if isinstance(entry, dict):
                    comp_id = entry.get('id')
                else:
                    comp_id = entry
                comp_info = components.get(comp_id, {})
                quality = comp_info.get('quality', 'unknown')
                print(f"  {comp_id} ({quality})")


@component.command("build-db")
@click.option("--output", "-o", default="components.json", help="Output file path")
@click.option("--format", "-f", type=click.Choice(['json', 'yaml']), default="json", help="Output format")
@click.option("--limit", "-l", type=int, help="Limit number of components to examine (for testing)")
@click.option("--sdk", "-s", help="Build database only for specified SDK ID (e.g., '2025.12.1')")
@click.pass_context
def component_build_db(ctx, output, format, limit, sdk):
    """Build component database for enhanced browsing"""
    import subprocess
    import sys

    print_success("Building component database...")

    # Check if SLC is available (optional)
    try:
        result = subprocess.run(['slc', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print_warning("SLC-CLI not found or not working; proceeding with .slcc file scanning")
    except FileNotFoundError:
        print_warning("SLC-CLI not found in PATH; proceeding with .slcc file scanning")

    # Import and run the database builder
    try:
        from build_component_db import build_component_database, save_database

        database = build_component_database(limit=limit, sdk_id=sdk)
        save_database(database, output, format)

        print_success(f"Component database saved to {output}")

    except ImportError:
        print_error("build_component_db.py not found. Make sure it's in the project directory.")
    except Exception as e:
        print_error(f"Failed to build database: {e}")


@component.command("list")
@click.option("--category", help="Filter by category (e.g., 'Platform|Driver')")
@click.option("--available", is_flag=True, help="Show only available components")
@click.option("--database", help="Path to component database file")
@click.pass_context
def component_list(ctx, category, available, database):
    """List project components"""
    if not ctx.obj["project_root"]:
        print_error("Not in a Silabs project directory")
        return

    project_root = ctx.obj["project_root"]

    if available:
        # Try to use component database first
        if database or _find_component_database():
            db_path = database or _find_component_database()
            components_data = _load_component_database(db_path)

            if components_data and category:
                # Filter by category using database
                _list_components_by_category(components_data, category)
                return
            elif components_data:
                # Show all available components from database
                _list_all_components_from_db(components_data)
                return

        # Fall back to slc-cli
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


def get_examples(slc_path: str, env: Dict[str, str]) -> Dict[str, Any]:
    """Parse slc examples -p output into structured data"""
    java_home = env.get('JAVA_HOME')
    if java_home:
        jar_path = str(Path(slc_path).parent / "slc.jar")
        cmd = f"{java_home}/bin/java -jar {jar_path} examples -p"
    else:
        cmd = f"{slc_path} examples -p"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
    
    if result.returncode != 0:
        print(f"ERROR: Failed to get examples: {result.stderr}", file=sys.stderr)
        return {}
    
    lines = result.stdout.split('\n')
    
    examples = {}
    current_package = None
    current_quality = None
    current_workspace = None
    current_project = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if line.startswith('Package:'):
            package_name = line.split(':', 1)[1].strip()
            current_package = package_name
            examples[current_package] = {}
        elif line.startswith('Quality:'):
            quality_name = line.split(':', 1)[1].strip()
            current_quality = quality_name
            if current_package:
                examples[current_package][current_quality] = {'workspaces': {}, 'projects': {}}
        elif line.startswith('Workspace:'):
            workspace_part = line.split(':', 1)[1].strip()
            if ' - ' in workspace_part:
                workspace_name, workspace_path = workspace_part.split(' - ', 1)
                workspace_name = workspace_name.strip()
                workspace_path = workspace_path.strip()
                if current_package and current_quality and workspace_path.endswith('.slcw'):
                    examples[current_package][current_quality]['workspaces'][workspace_name] = workspace_path
            else:
                current_workspace = workspace_part
        elif line.startswith('Project:'):
            project_part = line.split(':', 1)[1].strip()
            if ' - ' in project_part:
                project_name, project_path = project_part.split(' - ', 1)
                project_name = project_name.strip()
                project_path = project_path.strip()
                if current_package and current_quality and project_path.endswith('.slcp'):
                    examples[current_package][current_quality]['projects'][project_name] = project_path
            else:
                current_project = project_part
        elif current_workspace and line.endswith('.slcw'):
            if current_package and current_quality:
                examples[current_package][current_quality]['workspaces'][current_workspace] = line
        elif current_project and line.endswith('.slcp'):
            if current_package and current_quality:
                examples[current_package][current_quality]['projects'][current_project] = line
    
    return examples


def example_finder_ui(stdscr, slc_path: str, env: Dict[str, str]):
    """Curses UI for example finder"""
    curses.curs_set(0)
    stdscr.keypad(True)
    
    # Show loading message
    stdscr.addstr(0, 0, "Generating example list...")
    stdscr.refresh()
    
    # Get examples
    examples = get_examples(slc_path, env)
    if not examples:
        stdscr.addstr(0, 0, "No examples found")
        stdscr.getch()
        return
    
    # Navigation state
    state = 'packages'
    selected_package = None
    selected_quality = None
    selected_type = None  # 'workspaces' or 'projects'
    selected_item = None
    inputs = {'output_type': 'vscode'}  # default
    visible_start = 0
    
    packages = list(examples.keys())
    current_idx = 0
    
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        if state == 'packages':
            stdscr.addstr(0, 0, "Select Package:"[:width], curses.A_BOLD)
            menu_items = packages + ["Quit"]
            for i, item in enumerate(menu_items):
                if 2 + i >= height:
                    break
                attr = curses.A_REVERSE if i == current_idx else curses.A_NORMAL
                display = f"  {item}"[:width]
                stdscr.addstr(2 + i, 0, display, attr)
            
            key = stdscr.getch()
            if key == curses.KEY_UP and current_idx > 0:
                current_idx -= 1
            elif key == curses.KEY_DOWN and current_idx < len(menu_items) - 1:
                current_idx += 1
            elif key == ord('\n'):
                if current_idx < len(packages):
                    selected_package = packages[current_idx]
                    state = 'qualities'
                    qualities = list(examples[selected_package].keys())
                    current_idx = 0
                else:
                    break  # Quit
            elif key == ord('q'):
                break
        
        elif state == 'qualities':
            header = f"Package: {selected_package}"[:width]
            stdscr.addstr(0, 0, header, curses.A_BOLD)
            stdscr.addstr(1, 0, "Select Quality:"[:width])
            qualities = list(examples[selected_package].keys())
            menu_items = qualities + ["Back"]
            for i, item in enumerate(menu_items):
                if 3 + i >= height:
                    break
                attr = curses.A_REVERSE if i == current_idx else curses.A_NORMAL
                display = f"  {item}"[:width]
                stdscr.addstr(3 + i, 0, display, attr)
            
            key = stdscr.getch()
            if key == curses.KEY_UP and current_idx > 0:
                current_idx -= 1
            elif key == curses.KEY_DOWN and current_idx < len(menu_items) - 1:
                current_idx += 1
            elif key == ord('\n'):
                if current_idx < len(qualities):
                    selected_quality = qualities[current_idx]
                    state = 'type'
                    current_idx = 0
                else:
                    state = 'packages'
                    current_idx = packages.index(selected_package)
            elif key == ord('q'):
                break
        
        elif state == 'type':
            header = f"Package: {selected_package} > Quality: {selected_quality}"[:width]
            stdscr.addstr(0, 0, header, curses.A_BOLD)
            stdscr.addstr(1, 0, "Select Type:"[:width])
            types = []
            if examples[selected_package][selected_quality]['projects']:
                types.append('projects')
            if examples[selected_package][selected_quality]['workspaces']:
                types.append('workspaces')
            
            menu_items = types + ["Back"]
            for i, item in enumerate(menu_items):
                if 3 + i >= height:
                    break
                attr = curses.A_REVERSE if i == current_idx else curses.A_NORMAL
                display_item = item.title() if item != "Back" else item
                display = f"  {display_item}"[:width]
                stdscr.addstr(3 + i, 0, display, attr)
            
            key = stdscr.getch()
            if key == curses.KEY_UP and current_idx > 0:
                current_idx -= 1
            elif key == curses.KEY_DOWN and current_idx < len(menu_items) - 1:
                current_idx += 1
            elif key == ord('\n'):
                if current_idx < len(types):
                    selected_type = types[current_idx]
                    state = 'items'
                    items = list(examples[selected_package][selected_quality][selected_type].keys())
                    current_idx = 0
                    visible_start = 0
                else:
                    state = 'qualities'
                    visible_start = 0
                    current_idx = qualities.index(selected_quality)
                    current_idx = qualities.index(selected_quality)
            elif key == ord('q'):
                break
        
        elif state == 'items':
            header = f"Package: {selected_package} > Quality: {selected_quality} > {selected_type.title()}"[:width]
            stdscr.addstr(0, 0, header, curses.A_BOLD)
            stdscr.addstr(1, 0, "Select Item:"[:width])
            items = list(examples[selected_package][selected_quality][selected_type].keys())
            menu_items = items + ["Back"]
            visible_count = height - 4
            display_items = menu_items[visible_start : visible_start + visible_count]
            for i, item in enumerate(display_items):
                if 3 + i >= height:
                    break
                attr = curses.A_REVERSE if visible_start + i == current_idx else curses.A_NORMAL
                display = f"  {item}"[:width]
                stdscr.addstr(3 + i, 0, display, attr)
            
            key = stdscr.getch()
            if key == curses.KEY_UP:
                if current_idx > 0:
                    current_idx -= 1
                    if current_idx < visible_start:
                        visible_start = current_idx
            elif key == curses.KEY_DOWN:
                if current_idx < len(menu_items) - 1:
                    current_idx += 1
                    if current_idx >= visible_start + visible_count:
                        visible_start = max(0, current_idx - visible_count + 1)
            elif key == ord('\n'):
                if current_idx < len(items):
                    selected_item = items[current_idx]
                    state = 'settings'
                    current_idx = 0
                    visible_start = 0
                else:
                    state = 'type'
                    visible_start = 0
                    types = []
                    if examples[selected_package][selected_quality]['workspaces']:
                        types.append('workspaces')
                    if examples[selected_package][selected_quality]['projects']:
                        types.append('projects')
                    current_idx = types.index(selected_type)
            elif key == ord('q'):
                break
        
        elif state == 'settings':
            header = f"Selected: {selected_item}"[:width]
            stdscr.addstr(0, 0, header, curses.A_BOLD)
            stdscr.addstr(1, 0, "Settings:"[:width])
            menu_items = [
                f"Set project name ({inputs.get('project_name', 'default')})",
                f"Set output type ({inputs.get('output_type', 'vscode')})",
                f"Set project directory ({inputs.get('project_dir', 'default')})",
                f"Set board/device ({inputs.get('board_device', 'required')})",
                f"Set extra switches ({inputs.get('extra_switches', 'none')})",
                "Generate",
                "Back"
            ]
            visible_count = height - 4
            display_items = menu_items[visible_start : visible_start + visible_count]
            for i, item in enumerate(display_items):
                if 3 + i >= height:
                    break
                attr = curses.A_REVERSE if visible_start + i == current_idx else curses.A_NORMAL
                display = f"  {item}"[:width]
                stdscr.addstr(3 + i, 0, display, attr)
            
            key = stdscr.getch()
            if key == curses.KEY_UP:
                if current_idx > 0:
                    current_idx -= 1
                    if current_idx < visible_start:
                        visible_start = current_idx
            elif key == curses.KEY_DOWN:
                if current_idx < len(menu_items) - 1:
                    current_idx += 1
                    if current_idx >= visible_start + visible_count:
                        visible_start = max(0, current_idx - visible_count + 1)
            elif key == ord('\n'):
                if current_idx == 0:  # Set project name
                    stdscr.clear()
                    stdscr.addstr(0, 0, "Project Name (for -name): ")
                    curses.echo()
                    stdscr.refresh()
                    name = stdscr.getstr(0, 25, 50).decode('utf-8').strip()
                    if name:
                        inputs['project_name'] = name
                    curses.noecho()
                elif current_idx == 1:  # Set output type
                    output_types = ['cmake', 'iar', 'makefile', 'slsproj', 'vscode']
                    stdscr.clear()
                    stdscr.addstr(0, 0, "Select Output Type (-o):", curses.A_BOLD)
                    for i, typ in enumerate(output_types):
                        stdscr.addstr(2 + i, 0, f"{i+1}. {typ}")
                    stdscr.addstr(8, 0, "Choice (1-5): ")
                    stdscr.refresh()
                    choice = stdscr.getch()
                    if ord('1') <= choice <= ord('5'):
                        inputs['output_type'] = output_types[choice - ord('1')]
                elif current_idx == 2:  # Set project directory
                    stdscr.clear()
                    stdscr.addstr(0, 0, "Project Directory (-d): ")
                    curses.echo()
                    stdscr.refresh()
                    dir_ = stdscr.getstr(0, 25, 100).decode('utf-8').strip()
                    if dir_:
                        inputs['project_dir'] = dir_
                    curses.noecho()
                elif current_idx == 3:  # Set board/device
                    stdscr.clear()
                    stdscr.addstr(0, 0, "Board/Device (--with): ")
                    curses.echo()
                    stdscr.refresh()
                    bd = stdscr.getstr(0, 25, 50).decode('utf-8').strip()
                    if bd:
                        inputs['board_device'] = bd
                    curses.noecho()
                elif current_idx == 4:  # Set extra switches
                    stdscr.clear()
                    stdscr.addstr(0, 0, "Extra Switches: ")
                    curses.echo()
                    stdscr.refresh()
                    extra = stdscr.getstr(0, 18, 100).decode('utf-8').strip()
                    if extra:
                        inputs['extra_switches'] = extra
                    curses.noecho()
                elif current_idx == 5:  # Generate
                    if inputs.get('board_device'):
                        generate_command(slc_path, examples[selected_package][selected_quality][selected_type][selected_item], inputs, env)
                        break
                    else:
                        stdscr.clear()
                        stdscr.addstr(0, 0, "Board/Device is required. Press any key to continue.")
                        stdscr.refresh()
                        stdscr.getch()
                elif current_idx == 6:  # Back
                    state = 'items'
                    current_idx = items.index(selected_item)
                    visible_start = max(0, current_idx - visible_count + 1)
            elif key == ord('q'):
                break
        
        stdscr.refresh()


def get_user_inputs(stdscr, example_path: str) -> Optional[Dict[str, str]]:
    """Get user inputs for project generation"""
    curses.echo()
    height, width = stdscr.getmaxyx()
    
    inputs = {}
    
    # Project name
    stdscr.clear()
    stdscr.addstr(0, 0, "Project Name (for -name): ")
    stdscr.refresh()
    inputs['project_name'] = stdscr.getstr(0, 25, 50).decode('utf-8').strip()
    
    # Project output type
    output_types = ['cmake', 'iar', 'makefile', 'slsproj', 'vscode']
    stdscr.clear()
    stdscr.addstr(0, 0, "Select Output Type (-o):", curses.A_BOLD)
    for i, typ in enumerate(output_types):
        stdscr.addstr(2 + i, 0, f"{i+1}. {typ}")
    stdscr.addstr(8, 0, "Choice (1-5): ")
    stdscr.refresh()
    choice = stdscr.getch()
    if ord('1') <= choice <= ord('5'):
        inputs['output_type'] = output_types[choice - ord('1')]
    else:
        return None
    
    # Project directory
    stdscr.clear()
    stdscr.addstr(0, 0, "Project Directory (-d): ")
    stdscr.refresh()
    inputs['project_dir'] = stdscr.getstr(0, 25, 100).decode('utf-8').strip()
    
    # Board/Device
    stdscr.clear()
    stdscr.addstr(0, 0, "Board/Device (--with): ")
    stdscr.refresh()
    inputs['board_device'] = stdscr.getstr(0, 25, 50).decode('utf-8').strip()
    
    # Extra switches
    stdscr.clear()
    stdscr.addstr(0, 0, "Extra Switches: ")
    stdscr.refresh()
    inputs['extra_switches'] = stdscr.getstr(0, 18, 100).decode('utf-8').strip()
    
    curses.noecho()
    return inputs


def generate_command(slc_path: str, example_path: str, inputs: Dict[str, str], env: Dict[str, str]):
    """Generate the slc command"""
    # Set default project_dir if not set
    if not inputs.get('project_dir'):
        project_name = Path(example_path).stem
        inputs['project_dir'] = project_name
    
    java_home = env.get('JAVA_HOME')
    if java_home:
        jar_path = str(Path(slc_path).parent / "slc.jar")
        cmd = f"{java_home}/bin/java -jar {jar_path} generate \"{example_path}\" -np -cp"
    else:
        cmd = f"{slc_path} generate \"{example_path}\" -np -cp"
    
    if inputs.get('project_name'):
        cmd += f" -name \"{inputs['project_name']}\""
    
    if inputs.get('output_type'):
        cmd += f" -o {inputs['output_type']}"
    
    if inputs.get('project_dir'):
        cmd += f" -d \"{inputs['project_dir']}\""
    
    if inputs.get('board_device'):
        cmd += f" --with {inputs['board_device']}"
    
    if inputs.get('extra_switches'):
        cmd += f" {inputs['extra_switches']}"
    
    with open("last_slc_command.txt", "w") as f:
        f.write(cmd + "\n")
    print(f"Running: {cmd} (command saved to last_slc_command.txt)")
    result = subprocess.run(cmd, shell=True, env=env, capture_output=True, text=True)
    if result.returncode == 0:
        print_success("Project generated successfully")
    else:
        print_error("Project generation failed")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        with open("last_slc_output.txt", "w") as f:
            f.write("Command:\n" + cmd + "\n\nSTDOUT:\n" + result.stdout + "\n\nSTDERR:\n" + result.stderr + "\n")


@silabs.command()
@click.pass_context
def generate_example(ctx):
    """Interactive example project generator"""
    print("Starting generate-example")
    tool_manager = ctx.obj["tool_manager"]
    
    # Get SLC path
    slc_path = tool_manager.get_tool_path("slc-cli")
    if not slc_path:
        print_error("SLC-CLI not found in configuration")
        return
    
    # Get environment
    env = tool_manager.get_environment()
    
    # Launch the curses UI
    curses.wrapper(example_finder_ui, slc_path, env)


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
