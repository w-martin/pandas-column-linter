import subprocess
import unittest
from pathlib import Path


class TestPandasLinterIntegration(unittest.TestCase):
    def test_should_lint_example_file(self) -> None:
        # arrange
        example_file = Path("examples/typeddict_example.py").absolute()
        binary_path = Path(
            "rust_pandas_linter/target/debug/rust_pandas_linter",
        ).absolute()

        if not binary_path.exists():
            subprocess.run(["cargo", "build"], cwd="rust_pandas_linter", check=True)

        # act
        result = subprocess.run(
            [str(binary_path), str(example_file)],
            capture_output=True,
            text=True,
            check=True,
        )

        # assert
        assert "Column 'name' does not exist in UserSchema" in result.stdout

    def test_should_run_mypy_with_plugin(self) -> None:
        # arrange
        example_file = "examples/typeddict_example.py"
        binary_path = Path("rust_pandas_linter/target/debug/rust_pandas_linter")
        if not binary_path.exists():
            subprocess.run(["cargo", "build"], cwd="rust_pandas_linter", check=True)

        # act
        result = subprocess.run(
            ["mypy", example_file],
            capture_output=True,
            text=True,
            check=False,
        )

        # assert
        assert "Column 'name' does not exist in UserSchema" in result.stdout
        assert result.returncode == 1
