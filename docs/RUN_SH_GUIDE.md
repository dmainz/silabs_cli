# Generic run.sh Configuration Guide

## Overview

The `run.sh` script configures the Silabs CLI environment dynamically using the Silabs tool location service. This approach makes it **completely portable** across different machines and installations.

## How It Works

### 1. Tool Location Discovery

The script reads the Silabs tool location from:
```
~/.silabs/slt/slt.location
```

This file contains the path to the `slt` (Silabs Tool Locator) binary.

### 2. Dynamic Tool Lookup

Instead of hardcoding tool paths, the script uses:
```bash
slt where <tool-name>
```

This queries Silabs' tool registry (defined in `~/.silabs/tools.json`) to find tools dynamically:

**Found Tools:**
- `slc-cli` - Software Configuration tool
- `commander` - Device programmer
- `cmake` - Build system
- `ninja` - Build system  
- `gcc-arm-none-eabi` - ARM compiler toolchain
- `python` - Python interpreter
- `java21` - Java runtime (v21)

**Not Available (tested):**
- `arm-toolchain` - Not in Silabs tool registry (use `gcc-arm-none-eabi`)
- `make` - Listed in registry but not installed

### 3. PATH Configuration

The script automatically constructs the PATH with all tool locations, in this order:
1. **slt** directory - The primary Silabs Tool Locator itself
2. **Java** bin directory - Java executables
3. **GCC** toolchain - ARM compiler tools
4. **CMake** and **Ninja** - Build system tools

This ensures all tools (and slt itself) are accessible without needing full paths:

## Usage

### On macOS/Linux with Silabs Tools Installed

Simply run commands through the `run.sh` script:

```bash
# Show help
./run.sh --help

# Create a project
./run.sh create-project my_project

# Build
./run.sh build

# Flash
./run.sh flash
```

### Direct Python Usage

If you prefer to set up paths manually:

```bash
# Activate the venv
source activate.sh

# Then run silabs.py directly
python silabs.py --help
```

## Installation on Linux

### Step 1: Extract the Package
```bash
tar -xzf silabs-cli-linux-YYYYMMDD.tar.gz
cd silabs-cli-linux-export
```

### Step 2: Run Setup
```bash
./setup_linux.sh
```

### Step 3: Copy run.sh for Linux (Optional)

The `run.sh` script is cross-platform and works on Linux if Silabs tools are installed. If Silabs is not installed, use `activate.sh` instead:

```bash
source activate.sh
python silabs.py --help
```

## Environment Variables Set by run.sh

| Variable | Description |
|----------|-------------|
| `SLT_CLI` | Path to the Silabs Tool Locator binary |
| `SLC_CLI` | Path to slc-cli tool |
| `COMMANDER` | Path to device programmer |
| `CMAKE` | Path to CMake |
| `NINJA` | Path to Ninja build system |
| `GCC_ARM_NONE_EABI` | Path to ARM toolchain |
| `JAVA_HOME` | Java runtime (java21) location |
| `SILABS_PYTHON` | Python interpreter for Silabs |
| `PATH` | Updated with slt, Java, GCC, CMake, Ninja directories |

## Troubleshooting

### "slt.location not found"
This error means Silabs tools are not installed. Install them first:
- macOS: Install Simplicity Studio 6 or Simplicity Commander
- Linux: Install the Silabs tools on your system

### Tools not found by slt where

Check which tools are actually installed by querying the tool registry:
```bash
# View all supported tools
cat ~/.silabs/tools.json | grep -E '^\s*"[a-z-]+":\s*\[' | sed 's/.*"\([^"]*\)".*/\1/'

# Test a specific tool
/path/to/slt where <tool-name>
```

The `tools.json` file is the source of truth for what `slt where` can find.

### Mixing python versions

The script tries to use the Silabs-provided Python, but falls back to system Python. To force a specific Python:

```bash
export SILABS_PYTHON=/usr/bin/python3
./run.sh build
```

## Advanced: Extending for New Tools

To add support for additional tools, edit `run.sh` and add:

```bash
TOOL_PATH="$("$SLT_CLI" where tool-name 2>/dev/null || echo '')"
if [ -n "$TOOL_PATH" ]; then
    export MY_TOOL="$TOOL_PATH"
fi
```

## See Also

- [README.md](README.md) - Main documentation
- [SILABS_CLI_PLAN.md](SILABS_CLI_PLAN.md) - Implementation roadmap
