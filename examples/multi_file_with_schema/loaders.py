"""Data loaders that return typed frames.

Return type annotations (``-> PandasFrame[OrderSchema]``) are the bridge
between schema definitions and the cross-file index.  When the checker processes
``pipeline.py`` and sees ``orders = load_orders(path)``, it looks up
``load_orders`` in the project index, resolves its return schema to
``OrderSchema``, and then validates every column access on ``orders`` against
that schema — even though ``load_orders`` is defined in a different file.

No ``usecols=`` is required here because the return type annotation already
tells the checker which columns exist.  You still get a W001 warning on the
bare ``pd.read_csv`` call (columns unknown at the read site), but column access
on the *returned* typed frame in other files is fully validated.
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
    """Load order records and assert the OrderSchema.

    The return type annotation is what the checker indexes.  Call sites in
    other files see this function as returning ``PandasFrame[OrderSchema]``
    and get full column validation without needing to know what happens inside.
    """
    from typedframes.pandas import PandasFrame

    raw = pd.read_csv(path)
    return PandasFrame.from_schema(raw, OrderSchema)


def load_customers(path: str) -> PolarsFrame[CustomerSchema]:
    """Load customer records and assert the CustomerSchema."""
    raw = pl.read_csv(path)
    return cast("PolarsFrame[CustomerSchema]", raw)
