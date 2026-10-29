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
import subprocess
from datetime import datetime

# Ensure project root is in sys.path so modules resolve cleanly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from typing import List, Dict, Set

from analyzer.parser import UniversalASTParser
from analyzer.ai_engine import AIDocumentationEngine
from analyzer.doc_generator import DocumentationGenerator
from analyzer.utils import (
    load_config,
    get_git_diff_files,
    scan_directory,
    logger,
)


def get_current_commit_summary() -> str:
    """Retrieves short hash and commit message of current HEAD."""
    try:
        out = subprocess.check_output(
            ["git", "log", "-1", "--pretty=format:%h - %s"],
            stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
        return out if out else "Unknown Commit"
    except Exception:
        return "Unknown Commit"


def main():
    """CLI Entry point for executing the automated documentation workflow."""
    start_time = datetime.now()
    commit_summary = get_current_commit_summary()
    engines_used: Set[str] = set()

    logger.log_fn(f"========== Documentation Pipeline Started for [{commit_summary}] ==========")
    
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
                engines_used.add(explanation.engine_used)
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

    # --- Write Workspace Status Artifacts in output_dir (e.g. docs/) ---
    end_time = datetime.now()
    duration_sec = (end_time - start_time).total_seconds()
    os.makedirs(args.output_dir, exist_ok=True)
    engine_summary = ", ".join(sorted(engines_used)) if engines_used else "None"

    # 1. Update pipeline_execution.log (historical audit log of action runs)
    exec_log_file = os.path.join(args.output_dir, "pipeline_execution.log")
    try:
        with open(exec_log_file, "a", encoding="utf-8") as f:
            f.write(f"[{start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}] ACTION STARTED for commit [{commit_summary}]\n")
            f.write(f"  -> Scanned: {len(target_files)} file(s), Documented: {total_classes} component(s), Engine: {engine_summary}\n")
            f.write(f"[{end_time.strftime('%Y-%m-%d %H:%M:%S UTC')}] ACTION COMPLETED (Duration: {duration_sec:.2f}s)\n\n")
    except Exception as log_err:
        logger.log_error(f"Failed writing to '{exec_log_file}'", exc=log_err)

    # 2. Update PIPELINE_STATUS.md (clean Markdown overview for the repository)
    status_file = os.path.join(args.output_dir, "PIPELINE_STATUS.md")
    try:
        scanned_list_md = "".join([f"  - `{f}`\n" for f in target_files[:15]])
        if len(target_files) > 15:
            scanned_list_md += f"  - ... and {len(target_files) - 15} more\n"
        if not target_files:
            scanned_list_md = "  - *(No changed code files detected)*\n"

        status_content = (
            f"# Pipeline Execution Status\n\n"
            f"- **Status**: COMPLETED (SUCCESS)\n"
            f"- **Triggered Commit**: `{commit_summary}`\n"
            f"- **Action Started**: `{start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}`\n"
            f"- **Action Completed**: `{end_time.strftime('%Y-%m-%d %H:%M:%S UTC')}` (Duration: `{duration_sec:.2f}s`)\n"
            f"- **Documented Components**: `{total_classes}`\n"
            f"- **AI Engine(s) Used**: `{engine_summary}`\n\n"
            f"### Scanned Target Files\n"
            f"{scanned_list_md}\n"
            f"---\n"
            f"*Auto-generated by [jerry-fab/Doc-Gen-Pipeline](https://github.com/jerry-fab/Doc-Gen-Pipeline)*\n"
        )
        with open(status_file, "w", encoding="utf-8") as f:
            f.write(status_content)
    except Exception as status_err:
        logger.log_error(f"Failed writing to '{status_file}'", exc=status_err)

    logger.log_fn(f"========== Documentation Pipeline Completed (Duration: {duration_sec:.2f}s) ==========\n")


if __name__ == "__main__":
    main()
