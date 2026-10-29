#!/bin/sh
# ==============================================================================
# Installer for Doc-Gen Git Hook
# Usage:
#   ./install-git-hook.sh [path-to-target-repo]
# If no target repo is specified, it installs into the current working directory.
# ==============================================================================

set -e

PIPELINE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET_DIR="${1:-.}"

if [ ! -d "$TARGET_DIR/.git" ]; then
    echo "[Error] '$TARGET_DIR' is not a git repository (missing .git directory)."
    echo "Usage: $0 [path-to-your-local-git-repo]"
    exit 1
fi

HOOKS_DIR="$TARGET_DIR/.git/hooks"
mkdir -p "$HOOKS_DIR"

# Copy pre-commit hook
cp "$PIPELINE_ROOT/hooks/pre-commit" "$HOOKS_DIR/pre-commit"
chmod +x "$HOOKS_DIR/pre-commit"

# Configure Git to remember the pipeline path for this repo
git -C "$TARGET_DIR" config --local docgen.pipelinedir "$PIPELINE_ROOT"

echo "============================================================"
echo "[SUCCESS] Doc-Gen Pre-Commit Hook successfully installed!"
echo "Target Repository: $(cd "$TARGET_DIR" && pwd)"
echo "Hook Location:     $HOOKS_DIR/pre-commit"
echo "Pipeline Location: $PIPELINE_ROOT"
echo "============================================================"
echo "Whenever you run 'git commit' with .cs, .py, or .java files,"
echo "documentation will be auto-generated and included in the commit."
echo "No remote server changes are required."
echo "============================================================"
