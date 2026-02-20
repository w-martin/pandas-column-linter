"""Integration tests for typedframes checker."""

import json
import tempfile
import unittest
from pathlib import Path

from typedframes._rust_checker import build_project_index, check_file  # ty: ignore[unresolved-import]


class TestTypedFramesCheckerIntegration(unittest.TestCase):
    """Integration tests for the Rust checker."""

    def test_should_detect_missing_column(self) -> None:
        """Test that the checker detects missing columns."""
        # arrange
        example_file = str(Path("examples/typedframes_example.py").absolute())

        # act
        result = check_file(example_file)

        # assert
        self.assertIn("Column 'wrong_column' does not exist", result)

    def test_should_suggest_typo_correction(self) -> None:
        """Test that the checker suggests corrections for typos."""
        # arrange
        example_file = str(Path("examples/typedframes_example.py").absolute())

        # act
        result = check_file(example_file)

        # assert
        self.assertIn("did you mean 'user_id'?", result)

    def test_should_track_mutations(self) -> None:
        """Test that the checker tracks column mutations."""
        # arrange
        example_file = str(Path("examples/typedframes_example.py").absolute())

        # act
        result = check_file(example_file)

        # assert
        self.assertIn("mutation tracking", result)

    def test_should_run_via_python_extension(self) -> None:
        """Test that the Rust checker works via Python extension."""
        # arrange
        example_file = str(Path("examples/typedframes_example.py").absolute())

        # act
        result = check_file(example_file)

        # assert
        self.assertIn("wrong_column", result)
        self.assertIn("does not exist", result)

    def test_should_warn_about_reserved_method_names(self) -> None:
        """Test that the checker warns about column names that shadow pandas/polars methods."""
        # arrange
        source = """
from typedframes import BaseSchema, Column

class BadSchema(BaseSchema):
    mean = Column(type=float)
    user_id = Column(type=int)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(source)
            temp_file = f.name

        # act
        result = check_file(temp_file)
        errors = json.loads(result)

        # assert
        self.assertEqual(len(errors), 1)
        self.assertIn("mean", errors[0]["message"])
        self.assertIn("conflicts with a pandas/polars method", errors[0]["message"])

        # cleanup
        Path(temp_file).unlink()

    def test_should_build_project_index_with_schema_entries(self) -> None:
        """Test that build_project_index returns valid JSON containing schema column data."""
        # arrange
        schema_source = """
from typedframes import BaseSchema, Column

class ProductSchema(BaseSchema):
    product_id = Column(type=int)
    name = Column(type=str)
    price = Column(type=float)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "schema.py"
            schema_path.write_text(schema_source)

            # act
            result_json = build_project_index(tmpdir)
            index = json.loads(result_json)

            # assert
            self.assertIn("version", index)
            self.assertIn("files", index)
            schema_entries = {k: v for k, v in index["files"].items() if k.endswith("schema.py")}
            self.assertEqual(len(schema_entries), 1)
            entry = next(iter(schema_entries.values()))
            self.assertIn("ProductSchema", entry["schemas"])
            self.assertIn("product_id", entry["schemas"]["ProductSchema"])
            self.assertIn("name", entry["schemas"]["ProductSchema"])
            self.assertIn("price", entry["schemas"]["ProductSchema"])

    def test_should_catch_cross_file_column_error(self) -> None:
        """Test that the checker catches column errors when the schema is defined in another file."""
        # arrange
        loaders_source = """
from typedframes import BaseSchema, Column
from typedframes.pandas import PandasFrame

class UserSchema(BaseSchema):
    user_id = Column(type=int)
    email = Column(type=str)

def load_users() -> PandasFrame[UserSchema]:
    pass
"""
        pipeline_source = """
from loaders import load_users

df = load_users()
print(df["user_id"])
print(df["wrong_column"])
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "loaders.py").write_text(loaders_source)
            (root / "pipeline.py").write_text(pipeline_source)
            (root / "pyproject.toml").write_text("[tool.typedframes]\nenabled = true\n")

            # act
            build_project_index(tmpdir)
            result = check_file(str(root / "pipeline.py"))
            errors = json.loads(result)

            # assert
            messages = [e["message"] for e in errors]
            self.assertTrue(any("wrong_column" in m for m in messages))
            self.assertFalse(any("user_id" in m for m in messages))
