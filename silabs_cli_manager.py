#!/usr/bin/env python3
"""
Silabs CLI Manager - User-friendly interface for Simplicity Studio 6 projects
"""

import curses
import subprocess
import json
import os
from pathlib import Path

class SilabsCLIManager:
    def __init__(self, config_path=None):
        # Try .slconf first, then .slcc for backward compatibility
        if config_path is None:
            base_path = Path.home() / "Documents" / "silabs-cli"
            config_path = base_path / "project.slconf"
            if not config_path.exists():
                config_path = base_path / "project.slcc"
        self.config_path = config_path
        self.config = self.load_config()
        self.current_menu = "main"
        self.menu_stack = []

    def load_config(self):
        """Load the project.slcc configuration"""
        if self.config_path.exists():
            # Parse the INI-like format
            config = {}
            current_section = None
            with open(self.config_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('#') or not line:
                        continue
                    if line.startswith('[') and line.endswith(']'):
                        current_section = line[1:-1]
                        config[current_section] = {}
                    elif '=' in line and current_section:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        # Handle list values
                        if value.startswith('[') and value.endswith(']'):
                            value = [v.strip().strip('"\'') for v in value[1:-1].split(',')]
                        config[current_section][key] = value
            return config
        return {}

    def save_config(self):
        """Save the configuration back to file"""
        with open(self.config_path, 'w') as f:
            f.write("# project.slconf – basic configuration used by slc‑cli/slt‑cli\n")
            f.write("# edit the paths below to match the versions you have installed.\n\n")
            for section, values in self.config.items():
                f.write(f"[{section}]\n")
                for key, value in values.items():
                    if isinstance(value, list):
                        f.write(f"{key} = [\n")
                        for v in value:
                            f.write(f'    "{v}",\n')
                        f.write("]\n")
                    else:
                        f.write(f"{key} = {value}\n")
                f.write("\n")

    def run_command(self, cmd, cwd=None):
        """Run a shell command and return output"""
        try:
            result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return -1, "", str(e)

    def get_slc_path(self):
        """Get path to slc-cli"""
        tool_paths = self.config.get('core', {}).get('tool-path', [])
        for path in tool_paths:
            if 'slc_cli' in path or 'slc-cli' in path:
                return path
        return None

    def get_slt_path(self):
        """Get path to slt-cli"""
        # Assume slt-cli is in similar location or PATH
        return "slt"  # Adjust as needed

    def get_commander_path(self):
        """Get path to commander"""
        tool_paths = self.config.get('core', {}).get('tool-path', [])
        for path in tool_paths:
            if 'commander' in path.lower():
                return path
        return None

    def list_projects(self):
        """List existing projects"""
        # This would need to be implemented based on slc-cli commands
        return ["No projects found - implement project listing"]

    def create_project(self, name, sdk=None):
        """Create a new project"""
        slt_path = self.get_slt_path()
        if not slt_path:
            return "slt-cli not found in config"
        
        sdk_path = sdk or self.config.get('slc', {}).get('sdk-package-path', [None])[0]
        if not sdk_path:
            return "No SDK path configured"
        
        cmd = f"{slt_path} new --project {name} --sdk {sdk_path}"
        return self.run_command(cmd)

    def build_project(self, project_path):
        """Build a project"""
        slc_path = self.get_slc_path()
        if not slc_path:
            return "slc-cli not found in config"
        
        cmd = f"{slc_path}/slc build {project_path}"
        return self.run_command(cmd)

    def flash_device(self, project_path, device=None):
        """Flash to device"""
        commander_path = self.get_commander_path()
        if not commander_path:
            return "Commander not found in config"
        
        # This is simplified - would need proper commander commands
        cmd = f"{commander_path} flash {project_path}/build/*.hex"
        return self.run_command(cmd)

    def show_components(self, project_path):
        """Show available components for a project"""
        slc_path = self.get_slc_path()
        if not slc_path:
            return "slc-cli not found"
        
        cmd = f"{slc_path}/slc component list --project {project_path}"
        return self.run_command(cmd)

    def install_component(self, project_path, component):
        """Install a component"""
        slc_path = self.get_slc_path()
        if not slc_path:
            return "slc-cli not found"
        
        cmd = f"{slc_path}/slc component install {component} --project {project_path}"
        return self.run_command(cmd)

    def draw_menu(self, stdscr, title, options, selected_idx):
        """Draw a menu with title and options"""
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        # Title
        title_x = w // 2 - len(title) // 2
        stdscr.addstr(1, title_x, title, curses.A_BOLD)
        
        # Options
        for i, option in enumerate(options):
            x = w // 2 - len(option) // 2
            y = 3 + i
            if i == selected_idx:
                stdscr.addstr(y, x, option, curses.A_REVERSE)
            else:
                stdscr.addstr(y, x, option)
        
        # Instructions
        instructions = "Use arrow keys to navigate, Enter to select, q to quit"
        stdscr.addstr(h-2, w//2 - len(instructions)//2, instructions, curses.A_DIM)
        
        stdscr.refresh()

    def main_menu(self, stdscr):
        """Main menu interface"""
        curses.curs_set(0)
        current_row = 0
        
        menu_options = [
            "1. List Projects",
            "2. Create New Project", 
            "3. Build Project",
            "4. Flash Device",
            "5. Configure Components",
            "6. Edit Configuration",
            "7. Exit"
        ]
        
        while True:
            self.draw_menu(stdscr, "Silabs CLI Manager", menu_options, current_row)
            
            key = stdscr.getch()
            
            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(menu_options) - 1:
                current_row += 1
            elif key == curses.KEY_ENTER or key in [10, 13]:
                if current_row == 0:  # List Projects
                    projects = self.list_projects()
                    self.show_message(stdscr, "Projects", "\n".join(projects))
                elif current_row == 1:  # Create Project
                    self.create_project_menu(stdscr)
                elif current_row == 2:  # Build
                    self.build_menu(stdscr)
                elif current_row == 3:  # Flash
                    self.flash_menu(stdscr)
                elif current_row == 4:  # Components
                    self.components_menu(stdscr)
                elif current_row == 5:  # Edit Config
                    self.edit_config_menu(stdscr)
                elif current_row == 6:  # Exit
                    break
            elif key == ord('q'):
                break

    def show_message(self, stdscr, title, message):
        """Show a message dialog"""
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        # Title
        stdscr.addstr(1, w//2 - len(title)//2, title, curses.A_BOLD)
        
        # Message
        lines = message.split('\n')
        for i, line in enumerate(lines):
            if i < h - 4:
                stdscr.addstr(3 + i, 2, line)
        
        stdscr.addstr(h-2, w//2 - 10, "Press any key to continue", curses.A_DIM)
        stdscr.refresh()
        stdscr.getch()

    def create_project_menu(self, stdscr):
        """Menu for creating a new project"""
        # Simplified - would need input fields
        self.show_message(stdscr, "Create Project", "Project creation not yet implemented\nPress any key")

    def build_menu(self, stdscr):
        """Menu for building projects"""
        self.show_message(stdscr, "Build Project", "Build functionality not yet implemented\nPress any key")

    def flash_menu(self, stdscr):
        """Menu for flashing devices"""
        self.show_message(stdscr, "Flash Device", "Flash functionality not yet implemented\nPress any key")

    def components_menu(self, stdscr):
        """Menu for component configuration"""
        self.show_message(stdscr, "Components", "Component configuration not yet implemented\nPress any key")

    def edit_config_menu(self, stdscr):
        """Menu for editing configuration"""
        self.show_message(stdscr, "Edit Config", "Config editing not yet implemented\nPress any key")

def main():
    manager = SilabsCLIManager()
    curses.wrapper(manager.main_menu)

if __name__ == "__main__":
    main()