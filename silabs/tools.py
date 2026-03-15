"""
Tool management for Silabs CLI
Handles tool path resolution and environment setup
"""

import subprocess
import os
from pathlib import Path
from typing import Optional, Dict
from .config import Config


class ToolManager:
    """Manage Silabs tools and their paths"""
    
    def __init__(self, config: Config = None):
        """Initialize tool manager"""
        self.config = config or Config()
        # Get slt-cli path from config/tools.json, fallback to hardcoded path
        self.slt_cli = self.config.get_tool_path("slt-cli") or "/Applications/SimplicityInstaller.app/Contents/Resources/slt"
        self.tool_cache = {}
    
    def get_tool_path(self, tool_name: str) -> Optional[str]:
        """Get path to a tool, resolving via env vars, config, or slt where"""
        # Check cache first
        if tool_name in self.tool_cache:
            return self.tool_cache[tool_name]
        
        # Check environment variable override first
        env_var = f"SILABS_{tool_name.upper().replace('-', '_')}"
        env_path = os.environ.get(env_var)
        if env_path:
            self.tool_cache[tool_name] = env_path
            return env_path
        
        # Try config/tools.json
        path = self.config.get_tool_path(tool_name)
        if path:
            self.tool_cache[tool_name] = path
            return path
        
        # Try slt where command
        path = self._slt_where(tool_name)
        if path:
            self.tool_cache[tool_name] = path
            return path
        
        return None
    
    def _slt_where(self, tool_name: str) -> Optional[str]:
        """Resolve tool path using 'slt where' command"""
        try:
            result = subprocess.run(
                [self.slt_cli, "where", tool_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None
    
    def get_environment(self) -> Dict[str, str]:
        """Get environment dict with all tool paths"""
        env = os.environ.copy()
        
        # Set individual tool paths
        tools = {
            "SLT_CLI": self.slt_cli,
            "SLC_CLI": self.get_tool_path("slc-cli"),
            "JAVA_HOME": self._get_java_home(),
            "CMAKE": self.get_tool_path("cmake"),
            "NINJA": self.get_tool_path("ninja"),
            "GCC_ARM": self.get_tool_path("gcc-arm-none-eabi"),
            "COMMANDER": self.get_tool_path("commander"),
        }
        
        for key, value in tools.items():
            if value:
                env[key] = value
        
        # Set PATH with proper ordering
        path_components = [
            f"{self._get_java_home()}/bin" if self._get_java_home() else None,
            os.path.dirname(self.get_tool_path("gcc-arm-none-eabi") or ""),
            os.path.dirname(self.get_tool_path("cmake") or ""),
            os.path.dirname(self.get_tool_path("ninja") or ""),
        ]
        
        path_components = [p for p in path_components if p]
        
        if path_components:
            env["PATH"] = ":".join(path_components) + ":" + env.get("PATH", "")
        
        return env
    
    def _get_java_home(self) -> Optional[str]:
        """Get Java home directory"""
        java_path = self.get_tool_path("java21")
        if java_path:
            # Check for Contents/Home (macOS JRE)
            contents_home = Path(java_path) / "jre" / "Contents" / "Home"
            if contents_home.exists():
                return str(contents_home)
            # Check for jre/Contents/Home
            jre_contents_home = Path(java_path) / "Contents" / "Home"
            if jre_contents_home.exists():
                return str(jre_contents_home)
            # Fallback to jre
            jre_path = Path(java_path) / "jre"
            if jre_path.exists():
                return str(jre_path)
            return java_path
        
        # Fallback to Simplicity Studio JRE
        ss_jre = Path.home() / ".silabs" / "slt" / "installs" / "archive" / "v6-base-v6.1.2-230" / "SimplicityStudio-6.app" / "Contents" / "Eclipse" / "sts_back_end.app" / "Contents" / "Eclipse" / "plugins" / "org.eclipse.justj.openjdk.hotspot.jre.full.stripped.macosx.aarch64_21.0.6.v20250130-0529" / "jre"
        if ss_jre.exists():
            return str(ss_jre)
        
        return None
    
    def validate_tools(self) -> Dict[str, bool]:
        """Check if all required tools are available"""
        required_tools = ["slt-cli", "slc-cli", "cmake", "ninja", "gcc-arm-none-eabi"]
        status = {}
        
        for tool in required_tools:
            path = self.get_tool_path(tool)
            status[tool] = bool(path)
        
        return status
    
    def print_tool_status(self):
        """Print status of all tools"""
        status = self.validate_tools()
        
        print("Tool Status:")
        print("-" * 40)
        for tool, available in status.items():
            status_str = "✓ Found" if available else "✗ Not Found"
            path = self.get_tool_path(tool)
            print(f"  {tool:20s} {status_str}")
            if path:
                print(f"    → {path}")
