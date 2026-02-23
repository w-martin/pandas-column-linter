"""CLI entry point for typedframes checker."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


def _collect_python_files(path: Path) -> list[Path]:
    """Collect all .py files from a path (file or directory)."""
    if path.is_file():
        if path.suffix == ".py":
            return [path]
        return []
    return sorted(path.rglob("*.py"))


def _check_files(files: list[Path], *, use_index: bool = True) -> list[dict]:
    """Run the Rust checker on each file, returning all errors with file paths."""
    try:
        from typedframes._rust_checker import check_file  # ty: ignore[unresolved-import]
    except ImportError:
        msg = (
            "The Rust checker extension was not found. "
            "Ensure typedframes was installed from a wheel or built with: maturin develop"
        )
        print(msg, file=sys.stderr)
        sys.exit(1)

    all_errors = []
    for file_path in files:
        result_json = check_file(str(file_path), use_index)
        errors = json.loads(result_json)
        for error in errors:
            error["file"] = str(file_path)
        all_errors.extend(errors)
    return all_errors


def _format_human(errors: list[dict]) -> str:
    """Format errors as human-readable lines."""
    lines = []
    for error in errors:
        icon = "\u26a0" if error.get("severity") == "warning" else "\u2717"
        lines.append(f"{icon} {error['file']}:{error['line']} - {error['message']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    """Entry point for the typedframes CLI."""
    parser = argparse.ArgumentParser(prog="typedframes", description="Static analysis for DataFrame column schemas.")
    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser("check", help="Check Python files for column errors.")
    check_parser.add_argument("path", type=Path, help="File or directory to check.")
    check_parser.add_argument("--strict", action="store_true", help="Exit with code 1 if any errors are found.")
    check_parser.add_argument("--json", dest="json_output", action="store_true", help="Output results as JSON.")
    check_parser.add_argument("--no-index", action="store_true", help="Disable cross-file index.")
    check_parser.add_argument(
        "--no-warnings", action="store_true", help="Suppress all warnings (W001, W002). Overrides pyproject.toml."
    )

    args = parser.parse_args(argv)

    if args.command != "check":
        parser.print_help()
        sys.exit(2)

    _run_check(args)


def _print_results(files: list[Path], all_errors: list[dict], elapsed: float, *, json_output: bool) -> None:
    """Print check results in human-readable or JSON format."""
    errors_only = [e for e in all_errors if e.get("severity") != "warning"]
    warnings = [e for e in all_errors if e.get("severity") == "warning"]
    if json_output:
        print(json.dumps(all_errors, indent=2))
        return
    if all_errors:
        print(_format_human(all_errors))
        print()
    file_label = "file" if len(files) == 1 else "files"
    if errors_only or warnings:
        parts = []
        if errors_only:
            error_label = "error" if len(errors_only) == 1 else "errors"
            parts.append(f"{len(errors_only)} {error_label}")
        if warnings:
            warn_label = "warning" if len(warnings) == 1 else "warnings"
            parts.append(f"{len(warnings)} {warn_label}")
        summary = ", ".join(parts)
        print(f"\u2717 Found {summary} in {len(files)} {file_label} ({elapsed:.1f}s)")
    else:
        print(f"\u2713 Checked {len(files)} {file_label} in {elapsed:.1f}s")


def _run_check(args: argparse.Namespace) -> None:
    """Execute the check subcommand."""
    path: Path = args.path.resolve()

    if not path.exists():
        print(f"Error: path does not exist: {path}", file=sys.stderr)
        sys.exit(2)

    use_index = not args.no_index
    if path.is_dir() and use_index:
        try:
            from typedframes._rust_checker import build_project_index  # ty: ignore[unresolved-import]

            build_project_index(str(path))
        except ImportError:
            pass

    files = _collect_python_files(path)
    start = time.perf_counter()
    all_errors = _check_files(files, use_index=use_index)
    elapsed = time.perf_counter() - start

    if args.no_warnings:
        all_errors = [e for e in all_errors if e.get("severity") != "warning"]

    errors_only = [e for e in all_errors if e.get("severity") != "warning"]
    _print_results(files, all_errors, elapsed, json_output=args.json_output)

    if args.strict and errors_only:
        sys.exit(1)
