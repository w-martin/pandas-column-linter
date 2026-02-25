"""Unit tests for the typedframes CLI."""

import builtins
import json
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from typedframes.cli import _check_files, _collect_python_files, _format_human, main


class TestCli(unittest.TestCase):
    """Unit tests for the CLI entry point."""

    def test_should_print_help_when_no_command(self) -> None:
        """Test that running with no arguments prints help and exits 2."""
        # arrange / act / assert
        with self.assertRaises(SystemExit) as ctx:
            main([])
        self.assertEqual(ctx.exception.code, 2)

    def test_should_exit_2_for_nonexistent_path(self) -> None:
        """Test that a nonexistent path exits with code 2."""
        # arrange / act / assert
        with self.assertRaises(SystemExit) as ctx:
            main(["check", "/nonexistent/path/xyz"])
        self.assertEqual(ctx.exception.code, 2)

    def test_should_exit_1_when_checker_not_installed(self) -> None:
        """Test that a helpful error is shown when typedframes-checker is missing."""
        # arrange
        original_import = builtins.__import__

        def mock_import(name: str, *args: object, **kwargs: object) -> object:
            if name == "typedframes._rust_checker":
                raise ImportError(name)
            return original_import(name, *args, **kwargs)

        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "test.py"
            py_file.write_text("x = 1\n")

            captured = StringIO()

            # act / assert
            with (
                patch("builtins.__import__", side_effect=mock_import),
                patch("sys.stderr", captured),
                self.assertRaises(SystemExit) as ctx,
            ):
                _check_files([py_file])

            self.assertEqual(ctx.exception.code, 1)
            self.assertIn("Rust checker extension was not found", captured.getvalue())

    def test_should_collect_single_python_file(self) -> None:
        """Test collecting a single .py file."""
        # arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "test.py"
            py_file.write_text("x = 1")

            # act
            result = _collect_python_files(py_file)

            # assert
            self.assertEqual(result, [py_file])

    def test_should_skip_non_python_file(self) -> None:
        """Test that non-.py files are skipped."""
        # arrange
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            txt_file = Path(tmpdir) / "data.txt"
            txt_file.write_text("hello")

            # act
            result = _collect_python_files(txt_file)

            # assert
            self.assertEqual(result, [])

    def test_should_collect_python_files_from_directory(self) -> None:
        """Test recursive collection of .py files from a directory."""
        # arrange
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "a.py").write_text("x = 1")
            (root / "b.txt").write_text("hello")
            sub = root / "sub"
            sub.mkdir()
            (sub / "c.py").write_text("y = 2")

            # act
            result = _collect_python_files(root)

            # assert
            self.assertEqual(len(result), 2)
            names = [f.name for f in result]
            self.assertIn("a.py", names)
            self.assertIn("c.py", names)

    def test_should_format_human_readable_errors(self) -> None:
        """Test human-readable error formatting."""
        # arrange
        errors = [
            {"file": "src/foo.py", "line": 23, "col": 0, "message": "Column 'x' not in Schema"},
            {"file": "src/bar.py", "line": 10, "col": 0, "message": "Column 'y' not in Schema"},
        ]

        # act
        result = _format_human(errors)

        # assert
        self.assertIn("\u2717 src/foo.py:23 - Column 'x' not in Schema", result)
        self.assertIn("\u2717 src/bar.py:10 - Column 'y' not in Schema", result)

    def test_should_format_warning_with_warning_icon(self) -> None:
        """Test that warnings use the ⚠ icon and errors use ✗."""
        # arrange
        items = [
            {"file": "a.py", "line": 1, "col": 0, "message": "error msg", "severity": "error"},
            {"file": "b.py", "line": 2, "col": 0, "message": "warn msg", "severity": "warning"},
        ]

        # act
        result = _format_human(items)

        # assert
        self.assertIn("\u2717 a.py:1 - error msg", result)
        self.assertIn("\u26a0 b.py:2 - warn msg", result)

    def test_should_output_json_when_flag_set(self) -> None:
        """Test JSON output mode."""
        # arrange
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "clean.py"
            py_file.write_text("x = 1\n")

            captured = StringIO()

            # act
            with patch("sys.stdout", captured):
                main(["check", str(py_file), "--json"])

            # assert
            output = captured.getvalue()
            parsed = json.loads(output)
            self.assertIsInstance(parsed, list)

    def test_should_exit_0_when_strict_and_no_errors(self) -> None:
        """Test that --strict exits 0 when there are no errors."""
        # arrange
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "clean.py"
            py_file.write_text("x = 1\n")

            # act / assert — should not raise SystemExit
            main(["check", str(py_file), "--strict"])

    def test_should_exit_1_when_strict_and_errors(self) -> None:
        """Test that --strict exits 1 when there are errors."""
        # arrange
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "bad.py"
            py_file.write_text(
                "from typedframes import BaseSchema, Column\n"
                "\n"
                "class S(BaseSchema):\n"
                "    x = Column(type=int)\n"
                "\n"
                'df: "DataFrame[S]" = load()\n'
                'df["wrong"]\n'
            )

            # act / assert
            with self.assertRaises(SystemExit) as ctx:
                main(["check", str(py_file), "--strict"])
            self.assertEqual(ctx.exception.code, 1)

    def test_should_print_summary_for_clean_files(self) -> None:
        """Test that a summary line is printed for clean files."""
        # arrange
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "clean.py"
            py_file.write_text("x = 1\n")

            captured = StringIO()

            # act
            with patch("sys.stdout", captured):
                main(["check", str(py_file)])

            # assert
            output = captured.getvalue()
            self.assertIn("\u2713 Checked 1 file", output)

    def test_should_print_error_count_for_bad_files(self) -> None:
        """Test that error count is printed for files with errors."""
        # arrange
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "bad.py"
            py_file.write_text(
                "from typedframes import BaseSchema, Column\n"
                "\n"
                "class S(BaseSchema):\n"
                "    x = Column(type=int)\n"
                "\n"
                'df: "DataFrame[S]" = load()\n'
                'df["wrong"]\n'
            )

            captured = StringIO()

            # act
            with patch("sys.stdout", captured):
                main(["check", str(py_file)])

            # assert
            output = captured.getvalue()
            self.assertIn("\u2717 Found 1 error", output)

    def test_should_print_warning_count_in_summary(self) -> None:
        """Test that warning count appears in the summary line."""
        # arrange
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "warn.py"
            py_file.write_text("import pandas as pd\ndf = pd.read_csv('x.csv')\n")

            captured = StringIO()

            # act
            with patch("sys.stdout", captured):
                main(["check", str(py_file), "--no-index", "--strict-ingest"])

            # assert
            output = captured.getvalue()
            self.assertIn("1 warning", output)

    def test_should_not_exit_1_when_strict_and_only_warnings(self) -> None:
        """Test that --strict does not exit 1 when there are only warnings (no errors)."""
        # arrange
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "warn.py"
            py_file.write_text("import pandas as pd\ndf = pd.read_csv('x.csv')\n")

            # act / assert — should not raise SystemExit(1)
            main(["check", str(py_file), "--strict", "--no-index"])

    def test_should_check_directory(self) -> None:
        """Test checking an entire directory."""
        # arrange
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "a.py").write_text("x = 1\n")
            (root / "b.py").write_text("y = 2\n")

            captured = StringIO()

            # act
            with patch("sys.stdout", captured):
                main(["check", str(root)])

            # assert
            output = captured.getvalue()
            self.assertIn("\u2713 Checked 2 files", output)

    def test_should_check_directory_with_no_index(self) -> None:
        """Test that --no-index skips building the project index."""
        # arrange
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "a.py").write_text("x = 1\n")

            captured = StringIO()

            # act
            with patch("sys.stdout", captured):
                main(["check", str(root), "--no-index"])

            # assert
            output = captured.getvalue()
            self.assertIn("\u2713 Checked 1 file", output)

    def test_should_suppress_warnings_with_no_warnings_flag(self) -> None:
        """Test that --no-warnings suppresses W001/W002 warnings from output."""
        # arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "warn.py"
            py_file.write_text("import pandas as pd\ndf = pd.read_csv('x.csv')\n")

            captured = StringIO()

            # act
            with patch("sys.stdout", captured):
                main(["check", str(py_file), "--no-index", "--no-warnings"])

            # assert
            output = captured.getvalue()
            self.assertNotIn("warning", output)
            self.assertIn("\u2713 Checked 1 file", output)

    def test_should_still_show_errors_with_no_warnings_flag(self) -> None:
        """Test that --no-warnings suppresses warnings but preserves errors."""
        # arrange
        warning_error = {
            "file": "mixed.py",
            "line": 2,
            "col": 0,
            "code": "W002",
            "message": "Dropped column 'x' does not exist in Schema",
            "severity": "warning",
        }
        actual_error = {
            "file": "mixed.py",
            "line": 7,
            "col": 0,
            "code": "E001",
            "message": "Column 'wrong' not in Schema",
            "severity": "error",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "mixed.py"
            py_file.write_text("x = 1\n")

            captured = StringIO()

            # act
            with (
                patch("typedframes.cli._check_files", return_value=[warning_error, actual_error]),
                patch("sys.stdout", captured),
            ):
                main(["check", str(py_file), "--no-warnings"])

            # assert
            output = captured.getvalue()
            self.assertNotIn("W001", output)
            self.assertIn("Column 'wrong'", output)
            self.assertIn("1 error", output)

    def test_should_suppress_w001_by_default(self) -> None:
        """Test that W001 ingestion warnings are suppressed by default."""
        # arrange
        w001 = {
            "file": "f.py",
            "line": 1,
            "col": 0,
            "code": "W001",
            "message": "columns unknown at lint time",
            "severity": "warning",
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "f.py"
            py_file.write_text("x = 1\n")
            captured = StringIO()

            # act
            with (
                patch("typedframes.cli._check_files", return_value=[w001]),
                patch("sys.stdout", captured),
            ):
                main(["check", str(py_file)])

            # assert
            output = captured.getvalue()
            self.assertNotIn("columns unknown at lint time", output)
            self.assertIn("\u2713 Checked 1 file", output)

    def test_should_show_w001_with_strict_ingest_flag(self) -> None:
        """Test that --strict-ingest enables W001 ingestion warnings."""
        # arrange
        w001 = {
            "file": "f.py",
            "line": 1,
            "col": 0,
            "code": "W001",
            "message": "columns unknown at lint time",
            "severity": "warning",
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "f.py"
            py_file.write_text("x = 1\n")
            captured = StringIO()

            # act
            with (
                patch("typedframes.cli._check_files", return_value=[w001]),
                patch("sys.stdout", captured),
            ):
                main(["check", str(py_file), "--strict-ingest"])

            # assert
            output = captured.getvalue()
            self.assertIn("columns unknown at lint time", output)

    def test_should_not_crash_when_checker_not_installed_on_directory(self) -> None:
        """Test that a missing Rust extension when checking a directory exits with code 1."""
        # arrange
        original_import = builtins.__import__

        def mock_import(name: str, *args: object, **kwargs: object) -> object:
            if name == "typedframes._rust_checker":
                raise ImportError(name)
            return original_import(name, *args, **kwargs)

        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "test.py"
            py_file.write_text("x = 1\n")

            captured = StringIO()

            # act / assert
            with (
                patch("builtins.__import__", side_effect=mock_import),
                patch("sys.stderr", captured),
                self.assertRaises(SystemExit) as ctx,
            ):
                main(["check", str(tmpdir)])

            self.assertEqual(ctx.exception.code, 1)
            self.assertIn("Rust checker extension was not found", captured.getvalue())
