#!/bin/bash
# Silicon Labs CLI Startup Script
# This script initializes the Silabs CLI environment by:
# 1. Finding and configuring SLT tools first (to use their python3)
# 2. Setting up/activating Python virtual environment
# 3. Installing/verifying dependencies
#
# IMPORTANT: This script must be SOURCED, not executed.
# Usage: source start_cli.sh   or   . start_cli.sh

# Ensure this script is being sourced, not executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]] || [[ "${BASH_SOURCE[0]}" == "-bash" ]] && [[ -z "$ZSH_VERSION" ]]; then
    # Handle bash strict mode
    if [[ "$(basename ${BASH_SOURCE[0]})" == "start_cli.sh" ]]; then
        cat <<'EOF'
⚠️  start_cli.sh must be SOURCED to work correctly.
    Run:  source ./start_cli.sh   or   . ./start_cli.sh

    Executing it directly will only change a child shell but not your current
    environment. Virtual environment activation and environment variables will
    not persist.
EOF
        exit 1
    fi
fi

# Handle zsh sourcing detection
if [[ -n "$ZSH_VERSION" && "$0" != "-zsh" ]]; then
    if [[ "${ZSH_ARGZERO}" == "start_cli.sh" ]]; then
        cat <<'EOF'
⚠️  start_cli.sh must be SOURCED to work correctly.
    Run:  source ./start_cli.sh   or   . ./start_cli.sh

    Executing it directly will only change a child shell but not your current
    environment. Virtual environment activation and environment variables will
    not persist.
EOF
        return 1
    fi
fi

# ============================================================================
# STEP 1: Determine script location and silabs-cli root directory
# ============================================================================

# Get the directory where this script is located
# This works for both executed and sourced scripts
if [[ -n "${BASH_SOURCE[0]}" ]]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
    # Fallback for when BASH_SOURCE is not available (rare case)
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
fi

# The silabs-cli root directory is the parent of scripts/
SILABS_CLI_ROOT="$(dirname "$SCRIPT_DIR")"

echo "📍 Silabs CLI root: $SILABS_CLI_ROOT"
echo "📍 Scripts directory: $SCRIPT_DIR"

# ============================================================================
# STEP 2: Find and configure SLT (Silicon Labs Tools) first
# ============================================================================

echo ""
echo "🔍 Looking for Silicon Labs Tools (SLT)..."

SLT_LOCATION_FILE="$HOME/.silabs/slt/slt.location"

if [ ! -f "$SLT_LOCATION_FILE" ]; then
    echo "❌ Error: slt.location not found at $SLT_LOCATION_FILE"
    echo "Please ensure Silicon Labs tools are installed."
    echo "Visit: https://www.silabs.com/developers/mcu-development-tools"
    return 1
fi

# Read SLT path from slt.location (handles multiple line formats)
export SLT_CLI=$(cat "$SLT_LOCATION_FILE" | tr -d '\n' | xargs)

if [ -z "$SLT_CLI" ] || [ ! -f "$SLT_CLI" ]; then
    echo "❌ Error: Could not read valid SLT_CLI from $SLT_LOCATION_FILE"
    return 1
fi

echo "✓ Using SLT: $SLT_CLI"

# Remember original PATH so cleanup script can restore it
if [ -z "$ORIGINAL_PATH" ]; then
    export ORIGINAL_PATH="$PATH"
fi

# Use slt where <tool> to find tool locations dynamically
# This makes the script portable across different installations
# Available tool names are defined in ~/.silabs/tools.json
export SLC_CLI="$("$SLT_CLI" where slc-cli 2>/dev/null || echo '')"
export COMMANDER="$("$SLT_CLI" where commander 2>/dev/null || echo '')"

# Try tools - may return directories or files
CMAKE_PATH="$("$SLT_CLI" where cmake 2>/dev/null || echo '')"
NINJA_PATH="$("$SLT_CLI" where ninja 2>/dev/null || echo '')"
GCC_PATH="$("$SLT_CLI" where gcc-arm-none-eabi 2>/dev/null || echo '')"

export CMAKE="$CMAKE_PATH"
export NINJA="$NINJA_PATH"
export GCC_ARM_NONE_EABI="$GCC_PATH"

# Get Python from SLT (use system python as fallback)
PYTHON_PATH="$("$SLT_CLI" where python 2>/dev/null || echo '')"
if [ -n "$PYTHON_PATH" ]; then
    export SILABS_PYTHON="$PYTHON_PATH/bin/python3"
else
    export SILABS_PYTHON=$(which python3 || echo 'python3')
fi

# Optional Java (java21 is available in tools.json)
JAVA_PATH=$("$SLT_CLI" where java21 2>/dev/null || echo '')
if [ -n "$JAVA_PATH" ]; then
    # Handle macOS Java bundle structure
    if [ -d "$JAVA_PATH/jre/Contents/Home/bin" ]; then
        export JAVA_HOME="$JAVA_PATH/jre/Contents/Home"
    else
        export JAVA_HOME="$JAVA_PATH/jre"
    fi
fi

# Build PATH with tool locations (avoiding duplicates)
PATH_ADDITIONS=""

# Add slt itself to PATH (it's the primary tool locator)
if [ -f "$SLT_CLI" ]; then
    SLT_DIR=$(dirname "$SLT_CLI")
    PATH_ADDITIONS="$SLT_DIR:$PATH_ADDITIONS"
fi

# Add tool directories to PATH in order of priority
if [ -n "$JAVA_HOME" ] && [ -d "$JAVA_HOME/bin" ]; then
    PATH_ADDITIONS="$JAVA_HOME/bin:$PATH_ADDITIONS"
fi

if [ -n "$GCC_ARM_NONE_EABI" ] && [ -d "$GCC_ARM_NONE_EABI" ]; then
    PATH_ADDITIONS="$GCC_ARM_NONE_EABI:$PATH_ADDITIONS"
elif [ -n "$GCC_ARM_NONE_EABI" ] && [ -d "$GCC_ARM_NONE_EABI/bin" ]; then
    PATH_ADDITIONS="$GCC_ARM_NONE_EABI/bin:$PATH_ADDITIONS"
fi

# Handle cmake/ninja (may be files or in subdirectories)
if [ -n "$CMAKE_PATH" ]; then
    if [ -f "$CMAKE_PATH" ]; then
        CMAKE_DIR=$(dirname "$CMAKE_PATH")
        PATH_ADDITIONS="$CMAKE_DIR:$PATH_ADDITIONS"
    elif [ -d "$CMAKE_PATH/bin" ]; then
        PATH_ADDITIONS="$CMAKE_PATH/bin:$PATH_ADDITIONS"
    elif [ -d "$CMAKE_PATH" ]; then
        PATH_ADDITIONS="$CMAKE_PATH:$PATH_ADDITIONS"
    fi
fi

if [ -n "$NINJA_PATH" ]; then
    if [ -f "$NINJA_PATH" ]; then
        NINJA_DIR=$(dirname "$NINJA_PATH")
        PATH_ADDITIONS="$NINJA_DIR:$PATH_ADDITIONS"
    elif [ -d "$NINJA_PATH/bin" ]; then
        PATH_ADDITIONS="$NINJA_PATH/bin:$PATH_ADDITIONS"
    elif [ -d "$NINJA_PATH" ]; then
        PATH_ADDITIONS="$NINJA_PATH:$PATH_ADDITIONS"
    fi
fi

PATH_ADDITIONS="$SLC_CLI:$COMMANDER:$PATH_ADDITIONS"

if [ -n "$PATH_ADDITIONS" ]; then
    export PATH="$PATH_ADDITIONS$PATH"
fi

# ============================================================================
# STEP 3: Set up and activate Python virtual environment
# ============================================================================

echo ""

# Determine venv location (relative to silabs-cli root)
VENV_DIR="$SILABS_CLI_ROOT/venv"

# Check if virtual environment is already active
if [ -n "$VIRTUAL_ENV" ]; then
    echo "✓ Virtual environment is already active: $VIRTUAL_ENV"
    
    # Verify it matches the expected location
    if [ "$VIRTUAL_ENV" == "$VENV_DIR" ]; then
        echo "✓ Environment is correctly configured for this project"
    else
        echo "⚠️  Note: Using different venv than expected"
        echo "  Expected: $VENV_DIR"
        echo "  Current:  $VIRTUAL_ENV"
    fi
else
    # Virtual environment is not active
    if [ ! -d "$VENV_DIR" ]; then
        # Create new virtual environment using SLT's python
        echo "📦 Creating virtual environment with Python from SLT..."
        
        # Verify we have a valid Python executable
        if ! command -v "$SILABS_PYTHON" &> /dev/null; then
            echo "❌ Error: Cannot find Python at: $SILABS_PYTHON"
            return 1
        fi
        
        # Check Python version (require 3.8+)
        PYTHON_VERSION=$("$SILABS_PYTHON" -c 'import sys; print(".".join(map(str, sys.version_info[:2])))' 2>/dev/null || echo 'unknown')
        
        if "$SILABS_PYTHON" -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null; then
            echo "✅ Python $PYTHON_VERSION found (3.8+)"
        else
            echo "❌ Error: Python $PYTHON_VERSION is too old (need 3.8+)"
            return 1
        fi
        
        "$SILABS_PYTHON" -m venv "$VENV_DIR"
        
        if [ ! -d "$VENV_DIR" ]; then
            echo "❌ Error: Failed to create virtual environment"
            return 1
        fi
        echo "✓ Virtual environment created"
    else
        echo "📦 Found existing virtual environment at $VENV_DIR"
    fi
    
    # Activate virtual environment
    echo "🔧 Activating virtual environment..."
    # shellcheck source=/dev/null
    source "$VENV_DIR/bin/activate"
    
    if [ -z "$VIRTUAL_ENV" ]; then
        echo "❌ Error: Failed to activate virtual environment"
        return 1
    fi
    echo "✓ Virtual environment activated"
fi

# ============================================================================
# STEP 4: Install/Verify dependencies
# ============================================================================

echo ""
echo "📚 Checking dependencies..."

# Check if requirements.txt exists
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"

if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo "❌ Error: requirements.txt not found at $REQUIREMENTS_FILE"
    return 1
fi

# Check if we need to install dependencies
# (Only do this once during initial setup, not on every source)
if [ -z "$SILABS_CLI_INITIALIZED" ]; then
    echo "⬆️  Upgrading pip..."
    python -m pip install --upgrade pip -q
    
    echo "📥 Installing dependencies from requirements.txt..."
    python -m pip install -r "$REQUIREMENTS_FILE" -q
    
    # Verify installation
    if python -c "import click, toml, yaml" 2>/dev/null; then
        echo "✅ All dependencies installed successfully"
    else
        echo "❌ Error: Some dependencies failed to install"
        return 1
    fi
    
    export SILABS_CLI_INITIALIZED=1
else
    echo "✓ Dependencies already installed (skipping reinstall)"
fi

# ============================================================================
# STEP 5: Final verification and summary
# ============================================================================

echo ""
echo "======================================================================"
echo "🎉 Silabs CLI environment is ready!"
echo "======================================================================"
echo ""
echo "📋 Configuration Summary:"
echo "   Root directory:    $SILABS_CLI_ROOT"
echo "   Virtual env:       $VIRTUAL_ENV"
echo "   Python:            $(which python)"
echo "   SLT:               $SLT_CLI"
[ -n "$SLC_CLI" ] && echo "   SLC CLI:           $SLC_CLI" || echo "   SLC CLI:           Not found"
[ -n "$COMMANDER" ] && echo "   Commander:        $COMMANDER" || echo "   Commander:        Not found"
[ -n "$CMAKE" ] && echo "   CMake:             $CMAKE" || echo "   CMake:             Not found"
[ -n "$NINJA" ] && echo "   Ninja:             $NINJA" || echo "   Ninja:             Not found"
[ -n "$GCC_ARM_NONE_EABI" ] && echo "   GCC ARM:           $GCC_ARM_NONE_EABI" || echo "   GCC ARM:           Not found"
echo ""
echo "📝 Next steps:"
echo "   • Run: silabs.py --help"
echo "   • To exit: source ./scripts/quit_cli.sh"
echo ""
