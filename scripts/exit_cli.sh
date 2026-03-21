#!/bin/bash
# Deactivation / cleanup helper for Silabs CLI
# This script is intended to be sourced from the workspace root after you've
# finished using the Silabs CLI. Sourcing is required so the environment
# modifications (unsetting variables, restoring PATH) apply to the current
# shell. Running it normally will only affect a subshell.

# ensure we're being sourced, not executed
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    cat <<'EOF'
⚠️  exit_cli.sh must be sourced to work correctly.
    Run:  source ./exit_cli.sh   or   . ./exit_cli.sh

    Executing it directly will only change a child shell but not your current
    environment.
EOF
    exit 1
fi

if [[ -n "$VIRTUAL_ENV" ]]; then
    echo "🔒 Deactivating virtual environment..."
    deactivate
    echo "✅ Virtual environment deactivated."
else
    echo "💡 No virtual environment is currently active."
fi

# unset environment variables created by run.sh
vars=(SLT_CLI SLC_CLI COMMANDER CMAKE NINJA GCC_ARM_NONE_EABI SILABS_PYTHON JAVA_HOME)
for v in "${vars[@]}"; do
    # check if variable is set (works in both bash and zsh)
    if [[ -n "${(P)v}" ]]; then
        unset "$v"
        echo "🗑️  unset $v"
    fi
done

# restore PATH if we saved the original
if [[ -n "$ORIGINAL_PATH" ]]; then
    export PATH="$ORIGINAL_PATH"
    unset ORIGINAL_PATH
    echo "🔁 PATH restored to original value"
fi

# future cleanup hooks could be added here
