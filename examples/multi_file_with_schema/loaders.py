"""Data loaders that return typed frames.

The return type annotations (``-> PandasFrame[OrderSchema]``) are what the
checker indexes.  When ``pipeline.py`` calls ``load_orders(path)``, the checker
looks up the function in the project index, resolves its return type to
``OrderSchema``, and validates all downstream column access against that schema
— without any ``usecols=`` or annotation in ``pipeline.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pandas as pd
import polars as pl
from schemas import CustomerSchema, OrderSchema

if TYPE_CHECKING:
    from typedframes.pandas import PandasFrame
    from typedframes.polars import PolarsFrame


def load_orders(path: str) -> PandasFrame[OrderSchema]:
    """Load order records and assert OrderSchema."""
    from typedframes.pandas import PandasFrame

    raw = pd.read_csv(path, usecols=["order_id", "customer_id", "amount", "status"])
    return PandasFrame.from_schema(raw, OrderSchema)


def load_customers(path: str) -> PolarsFrame[CustomerSchema]:
    """Load customer records and assert CustomerSchema."""
    raw = pl.read_csv(path, columns=["customer_id", "name", "region"])
    return cast("PolarsFrame[CustomerSchema]", raw)
