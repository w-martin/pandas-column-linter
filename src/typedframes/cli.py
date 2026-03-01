"""CLI entry point for typedframes checker."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# ANSI escape sequences
_RESET = "\033[0m"
_BOLD = "\033[1m"
_BOLD_RED = "\033[1;31m"
_BOLD_GREEN = "\033[1;32m"
_BOLD_YELLOW = "\033[1;33m"


def _collect_python_files(path: Path) -> list[Path]:
    """Collect all .py files from a path (file or directory)."""
    if path.is_file():
        if path.suffix == ".py":
            return [path]
        return []
    return sorted(path.rglob("*.py"))


def _check_files(files: list[Path], *, index_bytes: bytes | None = None) -> list[dict]:
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
        result_json = check_file(str(file_path), index_bytes)
        errors = json.loads(result_json)
        for error in errors:
            error["file"] = str(file_path)
        all_errors.extend(errors)
    return all_errors


def _format_text(errors: list[dict], *, color: bool = False) -> str:
    """Format errors as text lines using ty-style file:line:col: severity[code] message."""
    lines = []
    for error in errors:
        severity = error.get("severity", "error")
        code = error.get("code", "")
        file_ = error["file"]
        line = error["line"]
        col = error["col"]
        message = error["message"]
        code_part = f"[{code}]" if code else ""
        if color:
            sev_colored = f"{_BOLD_RED}error{_RESET}" if severity == "error" else f"{_BOLD_YELLOW}warning{_RESET}"
            lines.append(f"{_BOLD}{file_}{_RESET}:{line}:{col}: {sev_colored}{code_part} {message}")
        else:
            lines.append(f"{file_}:{line}:{col}: {severity}{code_part} {message}")
    return "\n".join(lines)


def _format_github(errors: list[dict]) -> str:
    """Format errors as GitHub Actions workflow commands."""
    lines = []
    for error in errors:
        severity = error.get("severity", "error")
        code = error.get("code", "")
        file_ = error["file"]
        line = error["line"]
        col = error["col"]
        message = error["message"]
        title = code or severity
        lines.append(f"::{severity} file={file_},line={line},col={col},title={title}::{message}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    """Entry point for the typedframes CLI."""
    parser = argparse.ArgumentParser(prog="typedframes", description="Static analysis for DataFrame column schemas.")
    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser("check", help="Check Python files for column errors.")
    check_parser.add_argument("path", type=Path, help="File or directory to check.")
    check_parser.add_argument("--strict", action="store_true", help="Exit with code 1 if any errors are found.")
    check_parser.add_argument(
        "--output-format",
        choices=["text", "json", "github"],
        default="text",
        dest="output_format",
        help="Output format: text (default), json, or github (GitHub Actions annotations).",
    )
    # --json kept as a hidden alias for backward compatibility
    check_parser.add_argument(
        "--json",
        dest="output_format",
        action="store_const",
        const="json",
        help=argparse.SUPPRESS,
    )
    check_parser.add_argument("--no-index", action="store_true", help="Disable cross-file index.")
    check_parser.add_argument(
        "--no-warnings",
        action="store_true",
        help="Suppress all warnings (dropped-unknown-column and any enabled ingestion warnings).",
    )
    check_parser.add_argument(
        "--strict-ingest",
        action="store_true",
        help="Include untracked-dataframe warnings for bare DataFrame loads without usecols= or columns=.",
    )

    args = parser.parse_args(argv)

    if args.command != "check":
        parser.print_help()
        sys.exit(2)

    _run_check(args)


def _print_results(files: list[Path], all_errors: list[dict], elapsed: float, *, output_format: str) -> None:
    """Print check results in the requested format."""
    errors_only = [e for e in all_errors if e.get("severity") != "warning"]
    warnings = [e for e in all_errors if e.get("severity") == "warning"]

    if output_format == "json":
        print(json.dumps(all_errors, indent=2))
        return

    use_color = output_format == "text" and hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

    if output_format == "github":
        if all_errors:
            print(_format_github(all_errors))
        return

    # text format
    if all_errors:
        print(_format_text(all_errors, color=use_color))
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
        msg = f"\u2717 Found {summary} in {len(files)} {file_label} ({elapsed:.1f}s)"
        print(f"{_BOLD_RED}{msg}{_RESET}" if use_color else msg)
    else:
        msg = f"\u2713 Checked {len(files)} {file_label} in {elapsed:.1f}s"
        print(f"{_BOLD_GREEN}{msg}{_RESET}" if use_color else msg)


def _run_check(args: argparse.Namespace) -> None:
    """Execute the check subcommand."""
    path: Path = args.path.resolve()

    if not path.exists():
        original = args.path
        if original.is_absolute():
            print(f"Error: path does not exist: {path}", file=sys.stderr)
        else:
            print(f"Error: path does not exist: {original!r} (resolved to {path})", file=sys.stderr)
        sys.exit(2)

    index_bytes: bytes | None = None
    if path.is_dir() and not args.no_index:
        try:
            from typedframes._rust_checker import build_project_index  # ty: ignore[unresolved-import]

            index_bytes = build_project_index(str(path))
        except ImportError:
            pass

    files = _collect_python_files(path)
    start = time.perf_counter()
    all_errors = _check_files(files, index_bytes=index_bytes)
    elapsed = time.perf_counter() - start

    if not args.strict_ingest:
        all_errors = [e for e in all_errors if e.get("code") != "untracked-dataframe"]

    if args.no_warnings:
        all_errors = [e for e in all_errors if e.get("severity") != "warning"]

    errors_only = [e for e in all_errors if e.get("severity") != "warning"]
    _print_results(files, all_errors, elapsed, output_format=args.output_format)

    if args.strict and errors_only:
        sys.exit(1)
