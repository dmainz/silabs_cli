# Silabs CLI

A comprehensive command-line interface for Simplicity Studio 6 development, inspired by ESP-IDF's `idf.py` script.  Implements silabs.py using Silabs CLI tools slt, slc, and commander.  The goal is to replace the need to use the Simplicity Studio 6 IDE and to supplement the Simplicity VSCode extension.

NOTE: This project is in it's initial phase and many features are yet to be implemented.

## Unix Setup (Mac, Linux, etc.)

### Prerequisites
On Linux systems:
- It is recommended you have a python version >= 3.8 installed.
The Simplicity Studio v6 install has a version of python, but its curses library
may not be compatible with your system.  The curses library is used as a 
menuing UI for project creation and eventually component configuration.
- Make sure python3-venv is installed.  Virtual environment is used to keep
your shell clean when not using this CLI.

### Quick Start

From anywhere in your filesystem:

```bash
# Navigate to the silabs-cli directory
cd /path/to/silabs-cli

# Source the startup script (IMPORTANT: must be sourced, not executed)
source ./scripts/start_cli.sh
```

The `start_cli.sh` script will:
1. Find and configure Silicon Labs Tools (SLT)
2. Create a Python virtual environment (if needed)
3. Install project dependencies
4. Verify your environment is ready

### When Done

```bash
# Deactivate the environment and restore your shell state
cd /path/to/silabs-cli
source ./scripts/quit_cli.sh
```

### Important Notes

- **Must be sourced**: Use `source ./scripts/start_cli.sh`, not `./scripts/start_cli.sh`
- **Works from anywhere**: The script automatically finds the project root
- **SLT first**: Silicon Labs Tools are configured before Python setup so their Python3 is used
- **Smart activation**: If the venv is already active, setup is skipped but environment is verified

## Requirements

- **Silicon Labs Tools (SLT)** - Required for tool discovery (install via Silicon Labs website)
- **Python 3.8 or higher** - Will be used from your SLT installation if available
- **Bash/Zsh shell** - For running startup scripts
- **Internet connection** - For pip package downloads on first setup

## Dependencies

Python packages (automatically installed by `start_cli.sh`):
- `click>=8.0.0` - CLI framework
- `toml>=0.10.0` - TOML configuration parsing
- `PyYAML>=6.0` - YAML file handling for .slcp/.slcc files

See `scripts/requirements.txt` for the complete list.

## Project Structure

```
silabs-cli/
├── silabs.py                    # Main CLI entry point
├── silabs/                      # Core modules
│   ├── __init__.py
│   ├── commands.py              # CLI command definitions
│   ├── config.py                # Configuration management
│   ├── build_component_db.py    # Component database builder
│   ├── tools.py                 # Tool path management
│   ├── utils.py                 # Utility functions
│   └── __pycache__/
├── scripts/                     # Shell scripts and configuration
│   ├── start_cli.sh             # 🎯 Main startup script (unified)
│   ├── quit_cli.sh              # Deactivation/cleanup script
│   ├── requirements.txt         # Python dependencies
│   └── run.sh                   # Legacy run script (deprecated)
│   └── setup_linux.sh           # Legacy setup script (deprecated)
├── docs/                        # Documentation
│   ├── README.md
│   ├── SILABS_CLI_PLAN.md
│   ├── PHASE2_BUILD_OPS.md
│   ├── PHASE2_PROJECT_MGMT.md
│   └── PHASE3_COMPONENTS.md
├── debug/                       # Debug/cache directory
└── README.md                    # This file
```

## Features

- **Project Management**: Create projects from examples, list, and manage Simplicity Studio projects
- **Component Configuration**: Browse, install, and remove project components using native .slcp/.slcc files
- **Build & Flash**: Build projects with CMake/Ninja and flash to devices
- **Device Operations**: Monitor serial output, erase flash, get device info
- **Configuration**: Edit project configuration using native Silabs formats
- **Tool Integration**: Seamless integration with slc-cli, commander, and other Silabs tools

## Usage Examples

```bash
# Show help
python silabs.py --help

# Create a new project from example (interactive)
silabs create-project [NAME] --sdk SDK_ID [--target BOARD_DEVICE]

# Create a project with SDK selection menu (if --sdk not provided or invalid)
silabs create-project [NAME]

# Build a project
python silabs.py build

# List available components
python silabs.py component list

# List components in a specific category
python silabs.py component list --category "Platform|Driver"

# Build component database for enhanced browsing
python silabs.py component build-db

# Install a component
python silabs.py component install bluetooth

# Flash to device
python silabs.py flash

# Start serial monitor
python silabs.py monitor

# Show current configuration
python silabs.py menuconfig
```

## Component Database

For enhanced component browsing, you can build a local database of all available components:

```bash
# Build component database (JSON format)
python silabs.py component build-db

# Build with custom output
python silabs.py component build-db --output my_components.yaml --format yaml

# Or use the standalone module
python -m silabs.build_component_db --output components.json
```

The database enables fast category-based filtering without querying SLC-CLI repeatedly.

## Configuration

The CLI uses native Silabs configuration files:
- `.slcp` files - Project configuration (YAML format)
- `.slcc` files - Component configuration (YAML format)
- `.slconf` files - Tool configuration (TOML format)

## Development

This CLI integrates with Silicon Labs tools discovered and managed by SLT:
- **slt-cli** - Tool location service (finds other tools)
- **slc-cli** - Software configuration tool
- **commander** - Device flashing and management tool
- **cmake** - Build system
- **ninja** - Build tool
- **gcc-arm-none-eabi** - ARM embedded toolchain

All tools are discovered at startup via `start_cli.sh` and added to your PATH automatically.

For development, after sourcing `start_cli.sh`, you can modify code in `silabs/` and test with:
```bash
python silabs.py --help
```

## License

MIT License