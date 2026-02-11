"""Unit tests for to_pandera_schema."""

import builtins
import unittest
from typing import Any
from unittest.mock import patch

import pandera as pa

from typedframes import BaseSchema, Column, ColumnSet, MissingDependencyError
from typedframes.pandera import to_pandera_schema


class UserSchema(BaseSchema):
    """Test schema for user data."""

    user_id = Column(type=int)
    email = Column(type=str)
    age = Column(type=float)
    active = Column(type=bool)


class NullableSchema(BaseSchema):
    """Test schema with nullable column."""

    name = Column(type=str)
    age = Column(type=int, nullable=True)


class AliasSchema(BaseSchema):
    """Test schema with aliased column."""

    email = Column(type=str, alias="email_address")


class ExplicitColumnSetSchema(BaseSchema):
    """Test schema with explicit ColumnSet members."""

    timestamp = Column(type=str)
    temperatures = ColumnSet(members=["temp_1", "temp_2", "temp_3"], type=float)


class StringMemberColumnSetSchema(BaseSchema):
    """Test schema with a single string member ColumnSet."""

    label = ColumnSet(members="category", type=str)


class RegexColumnSetSchema(BaseSchema):
    """Test schema with regex ColumnSet."""

    user_id = Column(type=int)
    scores = ColumnSet(members=r"score_\d+", type=float, regex=True)


class StrictSchema(BaseSchema):
    """Test schema that disallows extra columns."""

    allow_extra_columns = False

    user_id = Column(type=int)


class AnyTypeSchema(BaseSchema):
    """Test schema with Any-typed column."""

    data = Column(type=Any)


class TestPanderaIntegration(unittest.TestCase):
    """Unit tests for to_pandera_schema."""

    def test_should_map_column_types(self) -> None:
        """Test that Python types are mapped to correct pandera column dtypes."""
        # act
        result = to_pandera_schema(UserSchema)

        # assert
        self.assertIsInstance(result, pa.DataFrameSchema)
        self.assertEqual(result.columns["user_id"].dtype, pa.Column(dtype=int).dtype)
        self.assertEqual(result.columns["email"].dtype, pa.Column(dtype=str).dtype)
        self.assertEqual(result.columns["age"].dtype, pa.Column(dtype=float).dtype)
        self.assertEqual(result.columns["active"].dtype, pa.Column(dtype=bool).dtype)

    def test_should_map_nullable_column(self) -> None:
        """Test that nullable=True propagates to pandera Column."""
        # act
        result = to_pandera_schema(NullableSchema)

        # assert
        self.assertFalse(result.columns["name"].nullable)
        self.assertTrue(result.columns["age"].nullable)

    def test_should_respect_column_alias(self) -> None:
        """Test that aliased columns use the alias as pandera column name."""
        # act
        result = to_pandera_schema(AliasSchema)

        # assert
        self.assertIn("email_address", result.columns)
        self.assertNotIn("email", result.columns)

    def test_should_map_column_set_explicit_members(self) -> None:
        """Test that explicit ColumnSet members create individual pandera Columns."""
        # act
        result = to_pandera_schema(ExplicitColumnSetSchema)

        # assert
        self.assertIn("temp_1", result.columns)
        self.assertIn("temp_2", result.columns)
        self.assertIn("temp_3", result.columns)
        self.assertEqual(result.columns["temp_1"].dtype, pa.Column(dtype=float).dtype)

    def test_should_map_column_set_string_member(self) -> None:
        """Test that a ColumnSet with a single string member creates one pandera Column."""
        # act
        result = to_pandera_schema(StringMemberColumnSetSchema)

        # assert
        self.assertIn("category", result.columns)
        self.assertEqual(result.columns["category"].dtype, pa.Column(dtype=str).dtype)

    def test_should_map_column_set_regex(self) -> None:
        """Test that regex ColumnSet creates a regex pandera Column."""
        # act
        result = to_pandera_schema(RegexColumnSetSchema)

        # assert
        self.assertIn(r"score_\d+", result.columns)
        self.assertTrue(result.columns[r"score_\d+"].regex)

    def test_should_set_strict_when_extra_columns_disallowed(self) -> None:
        """Test that allow_extra_columns=False maps to strict=True."""
        # act
        result = to_pandera_schema(StrictSchema)

        # assert
        self.assertTrue(result.strict)

    def test_should_not_set_strict_when_extra_columns_allowed(self) -> None:
        """Test that allow_extra_columns=True (default) maps to strict=False."""
        # act
        result = to_pandera_schema(UserSchema)

        # assert
        self.assertFalse(result.strict)

    def test_should_skip_dtype_for_any_type(self) -> None:
        """Test that Column with type=Any produces a pandera Column with no dtype check."""
        # act
        result = to_pandera_schema(AnyTypeSchema)

        # assert
        self.assertIsNone(result.columns["data"].dtype)

    def test_should_raise_missing_dependency_error_when_pandera_not_installed(self) -> None:
        """Test that MissingDependencyError is raised when pandera is not installed."""
        # arrange
        original_import = builtins.__import__

        def mock_import(name: str, *args: object, **kwargs: object) -> object:
            if name == "pandera":
                raise ImportError
            return original_import(name, *args, **kwargs)

        # act/assert
        with (
            patch("builtins.__import__", side_effect=mock_import),
            self.assertRaises(MissingDependencyError) as ctx,
        ):
            to_pandera_schema(UserSchema)

        self.assertEqual(ctx.exception.package, "pandera")
        self.assertEqual(ctx.exception.feature, "to_pandera_schema")
