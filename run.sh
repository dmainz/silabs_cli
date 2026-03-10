#!/bin/bash
# Run script for Silabs CLI Manager - Generic configuration using slt

# Activate virtual environment if it exists and not already in a venv
if [ -z "$VIRTUAL_ENV" ] && [ -d "venv" ]; then
    # shellcheck source=/dev/null
    source venv/bin/activate
fi

# Find and parse SLT_CLI from ~/.silabs/slt/slt.location
SLT_LOCATION_FILE="$HOME/.silabs/slt/slt.location"

if [ ! -f "$SLT_LOCATION_FILE" ]; then
    echo "❌ Error: slt.location not found at $SLT_LOCATION_FILE"
    echo "Please ensure Silabs tools are installed"
    exit 1
fi

# Read SLT path from slt.location (handles multiple line formats)
export SLT_CLI=$(cat "$SLT_LOCATION_FILE" | tr -d '\n' | xargs)

if [ -z "$SLT_CLI" ] || [ ! -f "$SLT_CLI" ]; then
    echo "❌ Error: Could not read valid SLT_CLI from $SLT_LOCATION_FILE"
    exit 1
fi

echo "✓ Using SLT: $SLT_CLI"

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

# Optional Python path (use system python as fallback)
PYTHON_PATH="$("$SLT_CLI" where python 2>/dev/null || echo '')"
if [ -n "$PYTHON_PATH" ]; then
    export SILABS_PYTHON="$PYTHON_PATH"
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
        export JAVA_HOME="$JAVA_PATH"
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

if [ -n "$PATH_ADDITIONS" ]; then
    export PATH="$PATH_ADDITIONS$PATH"
fi

# Show configuration (optional)
# echo "📋 Tool Configuration:"
# [ -n "$SLC_CLI" ] && echo "  ✓ SLC_CLI: $SLC_CLI" || echo "  ✗ SLC_CLI: Not found"
# [ -n "$COMMANDER" ] && echo "  ✓ COMMANDER: $COMMANDER" || echo "  ✗ COMMANDER: Not found"
# [ -n "$CMAKE" ] && echo "  ✓ CMAKE: $CMAKE" || echo "  ✗ CMAKE: Not found"
# [ -n "$NINJA" ] && echo "  ✓ NINJA: $NINJA" || echo "  ✗ NINJA: Not found"
# [ -n "$GCC_ARM_NONE_EABI" ] && echo "  ✓ GCC_ARM_NONE_EABI: $GCC_ARM_NONE_EABI" || echo "  ✗ GCC_ARM_NONE_EABI: Not found"

# Run the CLI
python3 silabs.py "$@"