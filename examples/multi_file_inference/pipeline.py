"""Illustrates the cross-file blind spot when no schema is defined.

``load_orders`` returns a plain ``pd.DataFrame``.  The checker has no way to
know which columns that DataFrame holds once the call crosses a file boundary,
so it cannot validate subscript access here — bad column names pass silently.

Compare with ``examples/multi_file_with_schema/pipeline.py``, where the same
call pattern produces a caught unknown-column error because the return type annotation
carries ``OrderSchema`` into the project index.
"""

from __future__ import annotations

from loaders import load_orders


def process(path: str) -> None:
    """Access columns after a cross-file load — checker is blind here."""
    orders = load_orders(path)

    # load_orders returns pd.DataFrame — the checker has no column information
    # at this call site.  The accesses below are not validated.
    print(orders["order_id"])  # no error — but also: no validation
    print(orders["revenue"])  # no error — 'revenue' does not exist, but the
    #                             checker cannot see that from this file alone
