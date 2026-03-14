# Silabs CLI

A comprehensive command-line interface for Simplicity Studio 6 development, inspired by ESP-IDF's `idf.py` architecture.  Implements a wrapper script, silabs.py, around Silabs CLI tools slt, slc, and commander.  The goal is to replace the need to use the Simplicity Studio 6 IDE and replace much of the functionality of the Simplicity VSCode extension.  Single step debugging is not implemented in this tool.

NOTE: This project is in it's initial phase and many features are yet to be implemented.

## Linux Setup

To set up this project on a Linux machine:

### Option 1: Direct Setup (Without Silabs Tools)
1. **Clone or copy the project files** to your Linux machine
2. **Run the setup script**:
   ```bash
   ./setup_linux.sh
   ```
3. **Activate the environment**:
   ```bash
   source activate.sh
   ```
4. **Use the CLI**:
   ```bash
   python silabs.py --help
   ```

### Option 2: With Silabs Tools Installed
If you have Silabs tools installed on your Linux system:
1. **Follow Option 1 above to set up the environment**
2. **Use `run.sh` for automatic tool detection**:
   ```bash
   ./run.sh --help
   ./run.sh build
   ./run.sh flash
   ```

The `run.sh` script automatically discovers Silabs tools using the `slt` tool locator, making it portable across different installations. See [RUN_SH_GUIDE.md](RUN_SH_GUIDE.md) for details.

### Option 3: Packaged Export
If you're exporting from macOS/Windows to Linux, use the packaging script:
```bash
./package_for_linux.sh
```
This creates a `silabs-cli-linux-YYYYMMDD.tar.gz` file that you can transfer to Linux and extract.

## What the Setup Script Does

The `setup_linux.sh` script will:
- ✅ Check for Python 3.8+ availability
- 📦 Create a Python virtual environment (`venv/`)
- 🔧 Activate the virtual environment
- ⬆️ Upgrade pip to the latest version
- 📚 Install all required dependencies from `requirements.txt`
- 🧪 Test the installation
- 📝 Create an `activate.sh` convenience script

## Requirements

- Python 3.8 or higher
- Bash shell
- Internet connection (for pip installs)

## Dependencies

- `click>=8.0.0` - CLI framework
- `toml>=0.10.0` - TOML configuration parsing
- `PyYAML>=6.0` - YAML file handling for .slcp/.slcc files

## Project Structure

```
silabs-cli/
├── silabs.py              # Main CLI entry point
├── silabs/                # Core modules
│   ├── __init__.py
│   ├── commands.py        # CLI command definitions
│   ├── config.py          # Configuration management
│   ├── tools.py           # Tool path management
│   └── utils.py           # Utility functions
├── requirements.txt       # Python dependencies
├── setup_linux.sh         # Linux setup script
├── activate.sh            # Environment activation script (created by setup)
├── SILABS_CLI_PLAN.md     # Implementation plan
└── README.md             # This file
```

## Features

- **Project Management**: Create, list, and manage Simplicity Studio projects
- **Component Configuration**: Browse, install, and remove project components using native .slcp/.slcc files
- **Build & Flash**: Build projects with CMake/Ninja and flash to devices
- **Device Operations**: Monitor serial output, erase flash, get device info
- **Configuration**: Edit project configuration using native Silabs formats
- **Tool Integration**: Seamless integration with slc-cli, commander, and other Silabs tools

## Usage Examples

```bash
# Show help
python silabs.py --help

# Create a new project
python silabs.py create-project my_project

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

# Or use the standalone script
python build_component_db.py --output components.json
```

The database enables fast category-based filtering without querying SLC-CLI repeatedly.

## Configuration

The CLI uses native Silabs configuration files:
- `.slcp` files - Project configuration (YAML format)
- `.slcc` files - Component configuration (YAML format)
- `.slconf` files - Tool configuration (TOML format)

## Development

This CLI integrates with Silabs tools:
- `slc-cli` - Software Configuration tool
- `commander` - Device flashing tool
- `slt-cli` - Tool location service

Make sure these tools are installed and configured on your system.

## License

MIT License