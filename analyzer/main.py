"""
analyzer.main
~~~~~~~~~~~~~

Command-Line Interface (CLI) and Orchestrator for the Code Documentation Pipeline.

Features:
    - Incremental Scanning: Analyzes only files modified in the latest Git commit (`--diff`).
    - Full Workspace Scanning: Recursively scans and parses all supported languages (`--all`).
    - Targeted Scanning: Inspects an individual file or directory (`--path <path>`).
    - Automated Catalog Updates: Maintains the central `docs/README.md` index.

Usage:
    python analyzer/main.py --all
    python analyzer/main.py --diff
    python analyzer/main.py --path sample_project/OrderService.cs
"""

import os
import sys

# Ensure project root is in sys.path so modules resolve cleanly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import subprocess
from typing import List, Dict

from analyzer.parser import UniversalASTParser
from analyzer.ai_engine import AIDocumentationEngine
from analyzer.doc_generator import DocumentationGenerator

# Extensions currently supported by the AST parser
SUPPORTED_EXTENSIONS = {".py", ".cs", ".java"}


def get_git_diff_files() -> List[str]:
    """
    Retrieves modified or newly added files from the latest git commit (HEAD~1 -> HEAD).
    
    Used by GitHub Actions to perform incremental documentation generation without
    re-processing untouched files in the repository.
    
    Returns:
        List of matching relative file paths.
    """
    try:
        cmd = ["git", "diff", "--name-only", "HEAD~1", "HEAD"]
        output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        files = [line.strip() for line in output.splitlines() if line.strip()]
        return [
            f for f in files
            if os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS and os.path.exists(f)
        ]
    except Exception:
        # Fallback if not inside a git repository or during the initial commit
        return []


def scan_directory(base_dir: str) -> List[str]:
    """
    Recursively discovers all supported source code files within a directory,
    skipping build artifacts, virtual environments, and hidden git folders.
    
    Args:
        base_dir: Directory path to scan.
        
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
            if os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS:
                matched.append(os.path.normpath(os.path.join(root, f)))
    return matched


def main():
    """CLI Entry point for executing the automated documentation workflow."""
    cli_parser = argparse.ArgumentParser(
        description="Automated Multi-Language Code Documentation Engine"
    )
    cli_parser.add_argument(
        "--diff",
        action="store_true",
        help="Only process files modified in the latest git commit (used in CI/CD)"
    )
    cli_parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Process a specific file or folder path"
    )
    cli_parser.add_argument(
        "--all",
        action="store_true",
        help="Process all source files across the workspace"
    )
    cli_parser.add_argument(
        "--output-dir",
        type=str,
        default="docs",
        help="Documentation output directory (default: 'docs')"
    )

    args = cli_parser.parse_args()

    # Determine list of files to process
    target_files = []
    if args.diff:
        print("[Mode] Git Diff detection (incremental modified files only)")
        target_files = get_git_diff_files()
        if not target_files:
            print("[Info] No modified files detected in latest commit. Scanning workspace as fallback.")
            target_files = scan_directory(".")
    elif args.path:
        if os.path.isfile(args.path):
            target_files = [args.path]
        elif os.path.isdir(args.path):
            target_files = scan_directory(args.path)
        else:
            print(f"[Error] Specified path '{args.path}' does not exist.")
            sys.exit(1)
    else:
        # Default behavior: scan all files
        target_files = scan_directory(".")

    print(f"[*] Discovered {len(target_files)} source file(s) for architectural analysis.")

    # Initialize processing engines
    ast_parser = UniversalASTParser()
    ai_engine = AIDocumentationEngine()
    doc_gen = DocumentationGenerator(output_dir=args.output_dir)

    catalog: Dict[str, List[str]] = {}
    total_classes = 0

    # Execute parsing and documentation generation
    for file_path in target_files:
        print(f"  -> Parsing: {file_path}")
        result = ast_parser.parse_file(file_path)
        if not result or not result.classes:
            continue

        lang_name = result.language.capitalize()
        if lang_name not in catalog:
            catalog[lang_name] = []

        for cls_meta in result.classes:
            print(f"     Found Class: {cls_meta.name} (Lines {cls_meta.start_line}-{cls_meta.end_line})")
            explanation = ai_engine.explain_class(cls_meta)
            out_file = doc_gen.generate_class_doc(cls_meta, explanation)
            catalog[lang_name].append(out_file)
            total_classes += 1

    # Update root catalog index
    if catalog:
        doc_gen.update_index(catalog)
        print(f"\n[Success] Generated documentation for {total_classes} class(es).")
        print(f"[Success] Catalog index updated at `{os.path.join(args.output_dir, 'README.md')}`.")
    else:
        print("\n[Notice] No classes found in the scanned files.")


if __name__ == "__main__":
    main()
