"""
analyzer.main
~~~~~~~~~~~~~

Command-Line Interface (CLI) and Orchestrator for the Code Documentation Pipeline.

Features:
    - Multi-Environment Support: Toggle between 'local' (Gemini/Groq) and 'production' (Mistral/Claude) via `--env`.
    - Reads centralized settings from `config.json`.
    - Incremental Scanning: Analyzes only files modified in the latest Git commit (`--diff`).
    - Full Workspace Scanning: Recursively scans and parses all supported languages (`--all`).
    - Targeted Scanning: Inspects an individual file or directory (`--path <path>`).
    - Automated Catalog Updates: Maintains the central `docs/README.md` index.

Usage:
    python analyzer/main.py --all --env local
    python analyzer/main.py --diff --env production
    python analyzer/main.py --path tests/sample_code/OrderService.cs
"""

import os
import sys

# Ensure project root is in sys.path so modules resolve cleanly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from typing import List, Dict

from analyzer.parser import UniversalASTParser
from analyzer.ai_engine import AIDocumentationEngine
from analyzer.doc_generator import DocumentationGenerator
from analyzer.utils import (
    load_config,
    get_git_diff_files,
    scan_directory,
)


def main():
    """CLI Entry point for executing the automated documentation workflow."""
    # 1. Load centralized configuration from config.json
    config = load_config()

    cli_parser = argparse.ArgumentParser(
        description="Automated Multi-Language Code Documentation Engine"
    )
    cli_parser.add_argument(
        "--env",
        type=str,
        default=config.active_profile,
        choices=["local", "production"],
        help=f"Target environment profile (default from config.json: '{config.active_profile}')"
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
        default=config.generator.output_dir,
        help=f"Documentation output directory (default from config.json: '{config.generator.output_dir}')"
    )

    args = cli_parser.parse_args()

    # Determine profile
    active_profile = config.get_profile(args.env)
    print(f"[*] Active Environment: '{args.env.upper()}' | Provider: '{active_profile.provider}' | Model: '{active_profile.model}'")

    # Determine list of files to process
    target_files = []
    supported_exts = set(config.scanner.supported_extensions)

    if args.diff:
        print("[Mode] Git Diff detection (incremental modified files only)")
        target_files = get_git_diff_files(supported_exts=supported_exts)
        if not target_files:
            print("[Info] No modified files detected in latest commit. Scanning workspace as fallback.")
            target_files = scan_directory(".", supported_exts=supported_exts)
    elif args.path:
        if os.path.isfile(args.path):
            target_files = [args.path]
        elif os.path.isdir(args.path):
            target_files = scan_directory(args.path, supported_exts=supported_exts)
        else:
            print(f"[Error] Specified path '{args.path}' does not exist.")
            sys.exit(1)
    else:
        # Default behavior: scan all files
        target_files = scan_directory(".", supported_exts=supported_exts)

    print(f"[*] Discovered {len(target_files)} source file(s) for architectural analysis.")

    # Initialize processing engines
    ast_parser = UniversalASTParser()
    ai_engine = AIDocumentationEngine(profile=active_profile)
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
