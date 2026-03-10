"""
Configuration management for Silabs CLI
Handles TOML parsing and tool path resolution
"""

import json
import toml
from pathlib import Path
from typing import Optional, Dict, Any


class Config:
    """Manage TOML configuration files and tool paths"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize config from .slconf file"""
        if config_path is None:
            config_path = self._find_config()
        
        self.config_path = config_path
        self.data = {}
        self.tools_data = {}
        self._config_cache = {}  # Cache for expensive operations
        self._cache_timestamp = None
        
        if self.config_path and self.config_path.exists():
            self.load()
        
        # Load tools.json for tool path resolution
        self._load_tools_json()
    
    def _find_config(self) -> Optional[Path]:
        """Find project.slconf in current directory or home"""
        # Check current working directory first
        local_slconf = Path.cwd() / "project.slconf"
        if local_slconf.exists():
            return local_slconf
        
        # Check home/Documents/silabs-cli
        home_slconf = Path.home() / "Documents" / "silabs-cli" / "project.slconf"
        if home_slconf.exists():
            return home_slconf
        
        return None
    
    def load(self):
        """Load configuration from TOML file"""
        if not self.config_path or not self.config_path.exists():
            return
        
        try:
            self.data = toml.load(self.config_path)
        except Exception as e:
            print(f"Error loading config {self.config_path}: {e}")
    
    def save(self):
        """Save configuration back to TOML file"""
        if not self.config_path:
            raise ValueError("No config path set")
        
        try:
            with open(self.config_path, 'w') as f:
                toml.dump(self.data, f)
        except Exception as e:
            print(f"Error saving config {self.config_path}: {e}")
    
    def _load_tools_json(self):
        """Load tools.json from ~/.silabs directory"""
        tools_json = Path.home() / ".silabs" / "tools.json"
        if tools_json.exists():
            try:
                with open(tools_json) as f:
                    self.tools_data = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load tools.json: {e}")
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get config value by section and key"""
        return self.data.get(section, {}).get(key, default)
    
    def set(self, section: str, key: str, value: Any):
        """Set config value"""
        if section not in self.data:
            self.data[section] = {}
        self.data[section][key] = value
    
    def get_tool_path(self, tool_name: str, version: str = None) -> Optional[str]:
        """Get tool path from tools.json with caching"""
        cache_key = f"tool_{tool_name}_{version or 'latest'}"
        
        # Check cache first
        if cache_key in self._config_cache:
            return self._config_cache[cache_key]
        
        # Look up in tools_data
        if tool_name not in self.tools_data:
            self._config_cache[cache_key] = None
            return None
        
        tools = self.tools_data[tool_name]
        if isinstance(tools, list):
            # If version specified, find that version
            if version:
                for tool in tools:
                    if tool.get("version") == version:
                        path = tool.get("path")
                        break
                else:
                    path = None
            else:
                # Return latest
                path = tools[0].get("path") if tools else None
        else:
            path = tools if isinstance(tools, str) else None
        
        # Special handling for slc-cli - the path is to the directory, executable is inside
        if tool_name == "slc-cli" and path:
            path = str(Path(path) / "slc")
        
        self._config_cache[cache_key] = path
        return path
    
    @property
    def core_tools(self) -> list:
        """Get tool paths from config"""
        return self.get("core", "tool-path", [])
    
    @property
    def sdk_paths(self) -> list:
        """Get SDK paths from config"""
        return self.get("slc", "sdk-package-path", [])
    
    @property
    def toolchain(self) -> Dict[str, str]:
        """Get toolchain configuration"""
        return self.data.get("toolchain", {})
