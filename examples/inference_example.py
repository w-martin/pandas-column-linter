"""Demonstrates aggressive column inference in typedframes.

The standalone checker infers column sets from data loading calls and method
chains — without requiring explicit schema annotations. This example shows:

  1. Full schema annotation  (best practice — no warnings)
  2. usecols / columns=      (inferred schema — no warnings)
  3. No columns specified    (W001 warning — columns unknown at lint time)
  4. Method chain inference  (select, drop, rename, assign, filter)

To suppress W001/W002 warnings project-wide, add to pyproject.toml:

    [tool.typedframes]
    warnings = false

Or pass --no-warnings to the CLI for a single run:

    typedframes check src/ --no-warnings
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
import polars as pl

from typedframes import BaseSchema, Column

if TYPE_CHECKING:
    from typedframes.pandas import PandasFrame
    from typedframes.polars import PolarsFrame


class UserData(BaseSchema):
    """User records schema."""

    user_id = Column(type=int)
    email = Column(type=str)
    age = Column(type=int)


# ---------------------------------------------------------------------------
# 1. Full schema annotation (best practice)
# ---------------------------------------------------------------------------
# Annotating the variable with a schema gives the checker complete column
# information. No warnings are generated.


def load_annotated() -> None:
    """Load with explicit schema annotation — full static checking."""
    df: PandasFrame[UserData] = pd.read_csv("users.csv")  # type: ignore[assignment]
    print(df["user_id"])
    print(df["email"])
    # Accessing df["username"] would error: Column 'username' not in UserData


# ---------------------------------------------------------------------------
# 2. Explicit usecols= — inferred schema, no warning
# ---------------------------------------------------------------------------
# Passing usecols= (pandas) or columns= / schema= (polars) lets the checker
# build an inferred column set. Column access is validated against it.


def load_with_usecols() -> None:
    """Load with usecols= — checker infers column set, no W001 warning."""
    df = pd.read_csv("users.csv", usecols=["user_id", "email"])
    print(df["user_id"])
    print(df["email"])
    # Accessing df["age"] would error: 'age' not in inferred column set


def load_polars_with_columns() -> None:
    """Polars read_csv with columns= — checker infers column set."""
    df = pl.read_csv("users.csv", columns=["user_id", "email"])
    print(df["user_id"])
    # Accessing df["age"] would error: 'age' not in inferred column set


# ---------------------------------------------------------------------------
# 3. No columns specified — W001 warning
# ---------------------------------------------------------------------------
# Without usecols/columns or a schema annotation, the checker cannot determine
# which columns the DataFrame contains. It emits a W001 warning instead of
# silently skipping column validation.
#
# Checker output:
#   warning inference_example.py:N - columns unknown at lint time; specify
#     `usecols`/`columns` or annotate: `df: PandasFrame[MySchema] = pd.read_csv(...)`


def load_without_columns() -> None:
    """Load without column info — generates W001 warning."""
    df = pd.read_csv("users.csv")
    df_pl = pl.read_csv("users.csv")
    print(df, df_pl)


# ---------------------------------------------------------------------------
# 4. Method chain inference
# ---------------------------------------------------------------------------
# The checker propagates inferred column sets through method chains.
# Row-preserving operations (filter, query, head, tail, sort_values, dropna,
# fillna, ffill, bfill, reset_index, ...) pass the column set through unchanged.


def method_chain_inference() -> None:
    """Demonstrate column set propagation through pandas method chains."""
    df: PandasFrame[UserData] = pd.read_csv("users.csv")  # type: ignore[assignment]

    # Subscript slice — inferred column set {user_id, email}
    small = df[["user_id", "email"]]
    print(small["user_id"])
    # Accessing small["age"] would error: 'age' not in inferred column set

    # Row filters pass the column set through unchanged
    filtered = small[small["user_id"] > 0]
    print(filtered["user_id"])
    # Accessing filtered["age"] would error: 'age' not in inferred column set

    # rename() updates the column set — old name removed, new name added
    renamed = small.rename(columns={"email": "email_address"})
    print(renamed["email_address"])
    # Accessing renamed["email"] would error: 'email' was renamed out

    # drop() removes columns from the inferred set
    trimmed = df.drop(columns=["age"])
    print(trimmed["user_id"])
    # Accessing trimmed["age"] would error: 'age' was dropped

    # assign() adds new columns to the inferred set
    augmented = df.assign(created_at="2024-01-01")
    print(augmented["created_at"])
    print(augmented["user_id"])
    # Accessing augmented["phone"] would error: 'phone' not in inferred column set


def polars_select_inference() -> None:
    """Demonstrate select() inference for polars."""
    df: PolarsFrame[UserData] = pl.read_csv("users.csv")  # type: ignore[assignment]

    # select() with a literal list — inferred column set {user_id, email}
    small = df.select(["user_id", "email"])
    print(small["user_id"])
    # Accessing small["age"] would error: 'age' not in inferred column set


# ---------------------------------------------------------------------------
# 5. Remaining gaps — where W002 still appears
# ---------------------------------------------------------------------------
# Even with inferred schemas, some patterns generate warnings.


def inference_gaps() -> None:
    """Show W002: dropping a column not present in the inferred set."""
    df: PandasFrame[UserData] = pd.read_csv("users.csv")  # type: ignore[assignment]

    # Dropping a column that the checker knows doesn't exist — W002 warning:
    # W002: Dropped column 'nonexistent' does not exist in UserData
    trimmed = df.drop(columns=["nonexistent"])
    print(trimmed)
