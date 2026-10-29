"""
analyzer.main
~~~~~~~~~~~~~

Command-Line Interface (CLI) and Orchestrator for the Code Documentation Pipeline.

Features:
    - Guided by `config.json`'s `"deployment_mode"` ('local' or 'production').
    - Multi-Channel Logging: Writes to logs/err_log/, logs/fn_log/, logs/quota_complete_log/.
    - Incremental Scanning: Analyzes only files modified in the latest Git commit (`--diff`).
    - Full Workspace Scanning: Recursively scans and parses all supported languages (`--all`).
    - Targeted Scanning: Inspects an individual file or directory (`--path <path>`).
    - Automated Catalog Updates: Maintains the central `docs/README.md` index.

Usage:
    python analyzer/main.py --all
    python analyzer/main.py --diff
    python analyzer/main.py --path analyzer/parser.py
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
    logger,
)


def main():
    """CLI Entry point for executing the automated documentation workflow."""
    logger.log_fn("========== Documentation Pipeline Started ==========")
    
    # 1. Load centralized configuration from config.json
    config = load_config()
    active_profile = config.get_active_profile()

    mode_info = f"Deployment Mode: '{config.deployment_mode.upper()}' | Provider: '{active_profile.provider}' | Model: '{active_profile.model}'"
    print(f"[*] {mode_info}")
    logger.log_fn(mode_info)

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
        default=config.generator.output_dir,
        help=f"Documentation output directory (default from config.json: '{config.generator.output_dir}')"
    )

    args = cli_parser.parse_args()

    # Determine list of files to process
    target_files = []
    supported_exts = set(config.scanner.supported_extensions)

    if args.diff:
        print("[Mode] Git Diff detection (incremental modified files only)")
        logger.log_fn("Scan Mode: Incremental Git Diff (HEAD~1 -> HEAD)")
        target_files = get_git_diff_files(supported_exts=supported_exts)
        if not target_files:
            print("[Info] No modified files detected in latest commit. Scanning workspace as fallback.")
            logger.log_fn("No git diff files found. Scanning workspace fallback.")
            target_files = scan_directory(".", supported_exts=supported_exts)
    elif args.path:
        if os.path.isfile(args.path):
            target_files = [args.path]
            logger.log_fn(f"Scan Mode: Single Target File ({args.path})")
        elif os.path.isdir(args.path):
            target_files = scan_directory(args.path, supported_exts=supported_exts)
            logger.log_fn(f"Scan Mode: Target Directory ({args.path})")
        else:
            err_msg = f"Specified path '{args.path}' does not exist."
            print(f"[Error] {err_msg}")
            logger.log_error(err_msg)
            sys.exit(1)
    else:
        # Default behavior: scan all files
        logger.log_fn("Scan Mode: Full Workspace Scan")
        target_files = scan_directory(".", supported_exts=supported_exts)

    summary_scan = f"Discovered {len(target_files)} source file(s) for architectural analysis."
    print(f"[*] {summary_scan}")
    logger.log_fn(summary_scan)

    # Initialize processing engines
    ast_parser = UniversalASTParser()
    ai_engine = AIDocumentationEngine(profile=active_profile)
    doc_gen = DocumentationGenerator(output_dir=args.output_dir)

    catalog: Dict[str, List[str]] = {}
    total_classes = 0

    # Execute parsing and documentation generation
    for file_path in target_files:
        print(f"  -> Parsing: {file_path}")
        logger.log_fn(f"Starting AST parse for: {file_path}")
        
        try:
            result = ast_parser.parse_file(file_path)
        except Exception as parse_exc:
            print(f"  [Error] Failed parsing {file_path}: {parse_exc}")
            logger.log_error(f"AST Parsing failure for file '{file_path}'", exc=parse_exc)
            continue

        if not result or not result.classes:
            logger.log_fn(f"No classes found in: {file_path}")
            continue

        lang_name = result.language.capitalize()
        if lang_name not in catalog:
            catalog[lang_name] = []

        for cls_meta in result.classes:
            print(f"     Found Class: {cls_meta.name} (Lines {cls_meta.start_line}-{cls_meta.end_line})")
            logger.log_fn(f"Processing Class '{cls_meta.name}' in '{file_path}' (Lines {cls_meta.start_line}-{cls_meta.end_line})")
            
            try:
                explanation = ai_engine.explain_class(cls_meta)
                print(f"     [Engine Used]: {explanation.engine_used}")
                out_file = doc_gen.generate_class_doc(cls_meta, explanation)
                catalog[lang_name].append(out_file)
                total_classes += 1
                logger.log_fn(f"Generated documentation artifact with [{explanation.engine_used}]: {out_file}")
            except Exception as doc_exc:
                print(f"  [Error] Failed generating doc for class '{cls_meta.name}': {doc_exc}")
                logger.log_error(f"Doc generation failure for class '{cls_meta.name}' in '{file_path}'", exc=doc_exc)

    # Update root catalog index
    if catalog:
        doc_gen.update_index(catalog)
        success_msg = f"Generated documentation for {total_classes} class(es). Catalog index updated at '{os.path.join(args.output_dir, 'README.md')}'."
        print(f"\n[Success] {success_msg}")
        logger.log_fn(success_msg)
    else:
        notice_msg = "No classes found in the scanned files."
        print(f"\n[Notice] {notice_msg}")
        logger.log_fn(notice_msg)

    logger.log_fn("========== Documentation Pipeline Completed ==========\n")


if __name__ == "__main__":
    main()
