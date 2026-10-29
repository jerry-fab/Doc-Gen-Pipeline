"""
analyzer.utils.git_utils
~~~~~~~~~~~~~~~~~~~~~~~~

Filesystem scanning, Git diff detection, and file filtering utilities.
"""

import os
import subprocess
from typing import List, Set

SUPPORTED_EXTENSIONS: Set[str] = {".py", ".cs", ".java"}


def get_git_diff_files(
    supported_exts: Set[str] = SUPPORTED_EXTENSIONS,
    staged: bool = False
) -> List[str]:
    """
    Retrieves modified or newly added files from Git.
    
    Args:
        supported_exts: Set of file extensions to include (.py, .cs, .java, etc.)
        staged: If True, inspects staged changes in the Git index (used in pre-commit hooks).
                If False, inspects changes between HEAD~1 and HEAD (used in CI/CD pipelines).
    
    Returns:
        List of matching relative file paths that exist on disk.
    """
    try:
        if staged:
            cmd = ["git", "diff", "--cached", "--name-only"]
        else:
            cmd = ["git", "diff", "--name-only", "HEAD~1", "HEAD"]

        output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        files = [line.strip() for line in output.splitlines() if line.strip()]
        return [
            f for f in files
            if os.path.splitext(f)[1].lower() in supported_exts and os.path.exists(f)
        ]
    except Exception:
        # Fallback if not inside a git repository or during the initial commit
        return []


def scan_directory(base_dir: str, supported_exts: Set[str] = SUPPORTED_EXTENSIONS) -> List[str]:
    """
    Recursively discovers all supported source code files within a directory,
    skipping build artifacts, virtual environments, and hidden git folders.
    
    Args:
        base_dir: Directory path to scan.
        supported_exts: Set of file extensions to include.
        
    Returns:
        List of normalized file paths.
    """
    matched = []
    ignored_dirs = {
        ".git", ".github", "docs", "venv", ".venv",
        "bin", "obj", "node_modules", "__pycache__", "build", "dist"
    }
    for root, dirs, files in os.walk(base_dir):
        # Prune ignored directories in-place
        dirs[:] = [d for d in dirs if d not in ignored_dirs]
        for f in files:
            if os.path.splitext(f)[1].lower() in supported_exts:
                matched.append(os.path.normpath(os.path.join(root, f)))
    return matched
