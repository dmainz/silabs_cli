"""
Silabs CLI - Command-line interface for Simplicity Studio 6 development
"""

__version__ = "0.1.0"
__author__ = "Silicon Labs"

from .config import Config
from .tools import ToolManager
from .utils import run_command, setup_environment
from .build_component_db import build_component_database, save_database

__all__ = ["Config", "ToolManager", "run_command", "setup_environment", "build_component_database", "save_database"]
