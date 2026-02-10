"""Unit tests for PandasFrame class."""

import unittest

import pandas as pd

from typedframes import BaseSchema, Column, ColumnGroup, ColumnSet
from typedframes.pandas import PandasFrame


class UserSchema(BaseSchema):
    """Test schema for user data."""

    user_id = Column(type=int)
    email = Column(type=str, alias="email_address")


class SensorSchema(BaseSchema):
    """Test schema with ColumnSet."""

    timestamp = Column(type=str)
    temperatures = ColumnSet(members=["temp_1", "temp_2"], type=float)


class GroupedSchema(BaseSchema):
    """Test schema with ColumnGroup."""

    user_id = Column(type=int)
    email = Column(type=str)
    all_fields = ColumnGroup(members=[user_id, email])


class TestPandasFrame(unittest.TestCase):
    """Unit tests for PandasFrame."""

    def test_should_create_from_schema(self) -> None:
        """Test that from_schema creates a typed PandasFrame."""
        # arrange
        raw_df = pd.DataFrame({"user_id": [1, 2], "email_address": ["a@b.com", "c@d.com"]})

        # act
        sut = PandasFrame.from_schema(raw_df, UserSchema)

        # assert
        self.assertIsInstance(sut, PandasFrame)
        self.assertEqual(sut.schema, UserSchema)

    def test_should_access_column_by_descriptor(self) -> None:
        """Test that columns can be accessed by schema Column descriptor."""
        # arrange
        raw_df = pd.DataFrame({"user_id": [1, 2], "email_address": ["a@b.com", "c@d.com"]})
        sut = PandasFrame.from_schema(raw_df, UserSchema)

        # act
        result = sut[UserSchema.user_id]

        # assert
        self.assertIsInstance(result, pd.Series)
        self.assertEqual(result.tolist(), [1, 2])

    def test_should_access_aliased_column_by_descriptor(self) -> None:
        """Test that aliased columns can be accessed by schema Column descriptor."""
        # arrange
        raw_df = pd.DataFrame({"user_id": [1, 2], "email_address": ["a@b.com", "c@d.com"]})
        sut = PandasFrame.from_schema(raw_df, UserSchema)

        # act
        result = sut[UserSchema.email]

        # assert
        self.assertIsInstance(result, pd.Series)
        self.assertEqual(result.tolist(), ["a@b.com", "c@d.com"])

    def test_should_access_column_set_by_descriptor(self) -> None:
        """Test that ColumnSet can be accessed by descriptor."""
        # arrange
        raw_df = pd.DataFrame({"timestamp": ["t1"], "temp_1": [20.0], "temp_2": [25.0]})
        sut = PandasFrame.from_schema(raw_df, SensorSchema)

        # act
        result = sut[SensorSchema.temperatures]

        # assert
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(list(result.columns), ["temp_1", "temp_2"])

    def test_should_access_column_group_by_descriptor(self) -> None:
        """Test that ColumnGroups can be accessed by descriptor."""
        # arrange
        raw_df = pd.DataFrame({"user_id": [1, 2], "email": ["a@b.com", "c@d.com"]})
        sut = PandasFrame.from_schema(raw_df, GroupedSchema)

        # act
        result = sut[GroupedSchema.all_fields]

        # assert
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(list(result.columns), ["user_id", "email"])

    def test_should_access_column_by_string_key(self) -> None:
        """Test that columns can be accessed by string key (standard pandas)."""
        # arrange
        raw_df = pd.DataFrame({"user_id": [1, 2], "email_address": ["a@b.com", "c@d.com"]})
        sut = PandasFrame.from_schema(raw_df, UserSchema)

        # act
        result = sut["user_id"]

        # assert
        self.assertIsInstance(result, pd.Series)
        self.assertEqual(result.tolist(), [1, 2])

    def test_should_access_columns_by_string_list(self) -> None:
        """Test that multiple columns can be accessed by list of strings."""
        # arrange
        raw_df = pd.DataFrame({"user_id": [1, 2], "email_address": ["a@b.com", "c@d.com"]})
        sut = PandasFrame.from_schema(raw_df, UserSchema)

        # act
        result = sut[["user_id", "email_address"]]

        # assert
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(list(result.columns), ["user_id", "email_address"])

    def test_should_filter_with_boolean_series(self) -> None:
        """Test that boolean series filtering preserves PandasFrame type."""
        # arrange
        raw_df = pd.DataFrame({"user_id": [1, 2], "email_address": ["a@b.com", "c@d.com"]})
        sut = PandasFrame.from_schema(raw_df, UserSchema)

        # act
        result = sut[sut["user_id"] > 1]

        # assert
        self.assertIsInstance(result, PandasFrame)
        self.assertEqual(result.schema, UserSchema)

    def test_should_preserve_type_after_selection(self) -> None:
        """Test that column selection preserves PandasFrame type."""
        # arrange
        raw_df = pd.DataFrame({"user_id": [1, 2], "email_address": ["a@b.com", "c@d.com"]})
        sut = PandasFrame.from_schema(raw_df, UserSchema)

        # act
        result = sut[["user_id"]]

        # assert
        self.assertIsInstance(result, PandasFrame)

    def test_should_convert_to_plain_pandas(self) -> None:
        """Test that to_pandas returns a plain DataFrame."""
        # arrange
        raw_df = pd.DataFrame({"user_id": [1, 2], "email_address": ["a@b.com", "c@d.com"]})
        sut = PandasFrame.from_schema(raw_df, UserSchema)

        # act
        result = sut.to_pandas()

        # assert
        self.assertIsInstance(result, pd.DataFrame)
        self.assertNotIsInstance(result, PandasFrame)

    def test_should_fallback_to_pandas_methods(self) -> None:
        """Test that standard pandas methods work."""
        # arrange
        raw_df = pd.DataFrame({"user_id": [1, 2], "email_address": ["a@b.com", "c@d.com"]})
        sut = PandasFrame.from_schema(raw_df, UserSchema)

        # act
        shape = sut.shape
        columns = list(sut.columns)

        # assert
        self.assertEqual(shape, (2, 2))
        self.assertEqual(columns, ["user_id", "email_address"])

    def test_should_preserve_type_after_merge(self) -> None:
        """Test that merge preserves PandasFrame type and schema."""
        # arrange
        df1 = pd.DataFrame({"user_id": [1, 2], "email_address": ["a@b.com", "c@d.com"]})
        df2 = pd.DataFrame({"user_id": [1, 2], "name": ["Alice", "Bob"]})
        sut = PandasFrame.from_schema(df1, UserSchema)

        # act
        result = sut.merge(df2, on="user_id")

        # assert
        self.assertIsInstance(result, PandasFrame)
        self.assertEqual(result.schema, UserSchema)
        self.assertEqual(len(result), 2)

    def test_should_preserve_type_after_join(self) -> None:
        """Test that df.join() preserves PandasFrame type and schema."""
        # arrange
        df1 = pd.DataFrame({"user_id": [1, 2], "email_address": ["a@b.com", "c@d.com"]})
        df2 = pd.DataFrame({"name": ["Alice", "Bob"]}, index=[0, 1])
        sut = PandasFrame.from_schema(df1, UserSchema)

        # act
        result = sut.join(df2)

        # assert
        self.assertIsInstance(result, PandasFrame)
        self.assertEqual(result.schema, UserSchema)

    def test_should_access_columns_after_merge(self) -> None:
        """Test that schema column access works after merge."""
        # arrange
        df1 = pd.DataFrame({"user_id": [1, 2], "email_address": ["a@b.com", "c@d.com"]})
        df2 = pd.DataFrame({"user_id": [1, 2], "name": ["Alice", "Bob"]})
        sut = PandasFrame.from_schema(df1, UserSchema)
        merged = sut.merge(df2, on="user_id")

        # act
        user_ids = merged[UserSchema.user_id]
        emails = merged[UserSchema.email]

        # assert
        self.assertEqual(user_ids.tolist(), [1, 2])
        self.assertEqual(emails.tolist(), ["a@b.com", "c@d.com"])

    def test_should_access_columns_after_filter(self) -> None:
        """Test that schema column access works after filtering."""
        # arrange
        raw_df = pd.DataFrame({"user_id": [1, 2, 3], "email_address": ["a@b.com", "c@d.com", "e@f.com"]})
        sut = PandasFrame.from_schema(raw_df, UserSchema)
        filtered = sut[sut["user_id"] > 1]

        # act
        user_ids = filtered[UserSchema.user_id]
        emails = filtered[UserSchema.email]

        # assert
        self.assertEqual(user_ids.tolist(), [2, 3])
        self.assertEqual(emails.tolist(), ["c@d.com", "e@f.com"])

    def test_should_access_columns_after_select(self) -> None:
        """Test that schema column access works after column selection."""
        # arrange
        raw_df = pd.DataFrame({"user_id": [1, 2], "email_address": ["a@b.com", "c@d.com"]})
        sut = PandasFrame.from_schema(raw_df, UserSchema)
        selected = sut[["user_id", "email_address"]]

        # act
        user_ids = selected[UserSchema.user_id]

        # assert
        self.assertEqual(user_ids.tolist(), [1, 2])

    def test_should_create_with_explicit_consumed_map(self) -> None:
        """Test that from_schema accepts a pre-computed consumed_map."""
        # arrange
        raw_df = pd.DataFrame({"timestamp": ["t1"], "temp_1": [20.0], "temp_2": [25.0]})
        consumed_map = {"temperatures": ["temp_1", "temp_2"]}

        # act
        sut = PandasFrame.from_schema(raw_df, SensorSchema, column_consumed_map=consumed_map)

        # assert
        self.assertIsInstance(sut, PandasFrame)
        self.assertEqual(sut._column_consumed_map, consumed_map)

    def test_should_fallback_to_pandas_when_no_schema(self) -> None:
        """Test that PandasFrame without schema works with standard pandas access."""
        # arrange
        sut = PandasFrame({"user_id": [1, 2], "email": ["a@b.com", "c@d.com"]})

        # act
        result = sut.shape

        # assert
        self.assertEqual(result, (2, 2))
