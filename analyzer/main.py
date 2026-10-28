import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import subprocess
from typing import List, Dict

from analyzer.parser import UniversalASTParser
from analyzer.ai_engine import AIDocumentationEngine
from analyzer.doc_generator import DocumentationGenerator

SUPPORTED_EXTENSIONS = {".py", ".cs", ".java"}

def get_git_diff_files() -> List[str]:
    """Retrieves modified/added files from the last commit."""
    try:
        cmd = ["git", "diff", "--name-only", "HEAD~1", "HEAD"]
        output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        files = [line.strip() for line in output.splitlines() if line.strip()]
        return [f for f in files if os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS and os.path.exists(f)]
    except Exception:
        # Fallback if no git repo or first commit
        return []

def scan_directory(base_dir: str) -> List[str]:
    """Recursively collects all supported source files."""
    matched = []
    ignored_dirs = {".git", ".github", "docs", "venv", ".venv", "bin", "obj", "node_modules", "__pycache__"}
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in ignored_dirs]
        for f in files:
            if os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS:
                matched.append(os.path.normpath(os.path.join(root, f)))
    return matched

def main():
    parser = argparse.ArgumentParser(description="Automated Multi-Language Code Documentation Engine")
    parser.add_argument("--diff", action="store_true", help="Only process files modified in the latest git commit")
    parser.add_argument("--path", type=str, default=None, help="Process a specific file or folder")
    parser.add_argument("--all", action="store_true", help="Process all source files in the repository")
    parser.add_argument("--output-dir", type=str, default="docs", help="Documentation output directory (default: docs)")

    args = parser.parse_args()

    target_files = []
    if args.diff:
        print("[Mode] Git Diff detection (modified files only)")
        target_files = get_git_diff_files()
        if not target_files:
            print("[Info] No supported source files modified in recent commit. Scanning full workspace as fallback.")
            target_files = scan_directory(".")
    elif args.path:
        if os.path.isfile(args.path):
            target_files = [args.path]
        elif os.path.isdir(args.path):
            target_files = scan_directory(args.path)
    else:
        # Default or --all
        target_files = scan_directory(".")

    print(f"[*] Found {len(target_files)} source files to analyze.")

    ast_parser = UniversalASTParser()
    ai_engine = AIDocumentationEngine()
    doc_gen = DocumentationGenerator(output_dir=args.output_dir)

    catalog: Dict[str, List[str]] = {}
    total_classes = 0

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

    if catalog:
        doc_gen.update_index(catalog)
        print(f"\n[Success] Generated documentation for {total_classes} class(es).")
        print(f"[Success] Catalog index updated at `{os.path.join(args.output_dir, 'README.md')}`.")
    else:
        print("\n[Notice] No classes found in the scanned files.")

if __name__ == "__main__":
    main()
