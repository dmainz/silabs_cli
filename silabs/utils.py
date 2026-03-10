"""
Utility functions for Silabs CLI
"""

import subprocess
import os
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import yaml


def run_command(
    cmd: str,
    cwd: Optional[Path] = None,
    env: Optional[Dict] = None,
    verbose: bool = False,
    capture_output: bool = False
) -> Tuple[int, str, str]:
    """
    Run a shell command and return exit code, stdout, stderr
    
    Args:
        cmd: Command to run
        cwd: Working directory
        env: Environment variables
        verbose: Print command and output
        capture_output: Capture stdout/stderr
    
    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    if verbose:
        print(f"Running: {cmd}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            env=env or os.environ.copy(),
            capture_output=capture_output,
            text=True
        )
        
        if verbose and capture_output:
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, end="")
        
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)


def load_yaml_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load YAML file and return dictionary"""
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print_error(f"Failed to load YAML file {file_path}: {e}")
        return None


def save_yaml_file(file_path: Path, data: Dict[str, Any]) -> bool:
    """Save dictionary to YAML file"""
    try:
        with open(file_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        return True
    except Exception as e:
        print_error(f"Failed to save YAML file {file_path}: {e}")
        return False


def backup_file(file_path: Path) -> bool:
    """Create backup of file with .bak extension"""
    if not file_path.exists():
        return True
    
    backup_path = file_path.with_suffix(file_path.suffix + '.bak')
    try:
        import shutil
        shutil.copy2(file_path, backup_path)
        return True
    except Exception as e:
        print_error(f"Failed to backup {file_path}: {e}")
        return False


def load_slcp_file(project_root: Path) -> Optional[Dict[str, Any]]:
    """Load project .slcp file"""
    slcp_path = project_root / f"{project_root.name}.slcp"
    if not slcp_path.exists():
        return None
    return load_yaml_file(slcp_path)


def save_slcp_file(project_root: Path, config: Dict[str, Any]) -> bool:
    """Save project .slcp file with backup"""
    slcp_path = project_root / f"{project_root.name}.slcp"
    
    # Create backup if file exists
    if slcp_path.exists():
        backup_file(slcp_path)
    
    return save_yaml_file(slcp_path, config)


def load_slcc_file(component_path: Path) -> Optional[Dict[str, Any]]:
    """Load component .slcc file"""
    slcc_path = component_path.with_suffix('.slcc')
    if not slcc_path.exists():
        return None
    return load_yaml_file(slcc_path)


def setup_environment(env: Dict) -> Dict:
    """Set up environment for Silabs tools"""
    new_env = os.environ.copy()
    new_env.update(env)
    return new_env


def find_project_root(start_path: Path = None) -> Optional[Path]:
    """
    Find project root by looking for CMakeLists.txt or project.slconf
    
    Args:
        start_path: Starting directory (default: cwd)
    
    Returns:
        Path to project root or None
    """
    if start_path is None:
        start_path = Path.cwd()
    
    current = Path(start_path).resolve()
    
    while current != current.parent:
        if (current / "CMakeLists.txt").exists():
            return current
        if (current / "project.slconf").exists():
            return current
        current = current.parent
    
    return None


def get_build_dir(project_root: Path, custom_build_dir: Path = None) -> Path:
    """Get build directory for project"""
    if custom_build_dir:
        return custom_build_dir.resolve()
    return (project_root / "build").resolve()


def ensure_build_dir(build_dir: Path):
    """Create build directory if it doesn't exist"""
    build_dir.mkdir(parents=True, exist_ok=True)


def validate_project(project_root: Path) -> bool:
    """Check if directory is a valid Silabs project"""
    return (project_root / "CMakeLists.txt").exists() or \
           (project_root / "project.slconf").exists() or \
           (project_root / "project.slcc").exists()


def print_error(message: str):
    """Print error message"""
    print(f"ERROR: {message}")


def print_warning(message: str):
    """Print warning message"""
    print(f"WARNING: {message}")


def print_info(message: str):
    """Print info message"""
    print(f"INFO: {message}")


def print_success(message: str):
    """Print success message"""
    print(f"✓ {message}")
