"""Data transformations — column sets propagate through method chains.

The checker tracks how each structural operation modifies the inferred column
set and validates every downstream access against the updated set.

Structural operations and their effect on the inferred column set:

    Operation                        Effect
    ─────────────────────────────────────────────────────────────
    df[["a", "b"]]                   narrowed to {a, b}
    df.rename(columns={"a": "z"})    "a" removed, "z" added
    df.drop(columns=["a"])           "a" removed
    df.assign(x=...)                 "x" added
    df.select(["a"])            (pl) narrowed to {a}
    df.drop(["a"])              (pl) "a" removed

Row-preserving operations (filter, query, sort_values, head, tail, dropna, …)
pass the column set through unchanged.
"""

from __future__ import annotations

import pandas as pd
import polars as pl

AMOUNT_THRESHOLD = 500


# ---------------------------------------------------------------------------
# rename / drop / assign chain (pandas)
# ---------------------------------------------------------------------------


def normalise_orders(path: str) -> pd.DataFrame:
    """Rename, drop, and enrich an orders frame — checker follows every step."""
    # Checker infers {order_id, customer_id, amount, status}
    orders = pd.read_csv(path, usecols=["order_id", "customer_id", "amount", "status"])

    # rename: customer_id → user_id  (checker removes "customer_id", adds "user_id")
    renamed = orders.rename(columns={"customer_id": "user_id"})
    print(renamed["user_id"])  # ✓ OK — new name
    # Accessing renamed["customer_id"] would error: 'customer_id' renamed to 'user_id'

    # drop: remove status — not needed downstream
    public = renamed.drop(columns=["status"])
    print(public["order_id"])  # ✓ OK
    # Accessing public["status"] would error: 'status' was dropped

    # assign: add a derived column — checker adds it to the inferred set
    enriched = public.assign(amount_vat=public["amount"] * 1.2)
    print(enriched["amount_vat"])  # ✓ OK — newly added
    # Accessing enriched["discount"] would error: 'discount' not in inferred set

    return enriched


# ---------------------------------------------------------------------------
# Multi-column subscript narrowing (pandas)
# ---------------------------------------------------------------------------


def slim_for_report(path: str) -> pd.DataFrame:
    """Slice to a subset of columns — inferred set narrows accordingly."""
    orders = pd.read_csv(path, usecols=["order_id", "customer_id", "amount", "status"])

    # Subscript with a list — inferred set narrows to {order_id, amount}
    slim = orders[["order_id", "amount"]]
    print(slim["order_id"])  # ✓ OK
    # Accessing slim["customer_id"] would error: 'customer_id' not in sliced set

    # Row filter — column set passes through unchanged
    big = slim[slim["amount"] > AMOUNT_THRESHOLD]
    print(big["amount"])  # ✓ OK — still {order_id, amount}
    # Accessing big["status"] would error: 'status' not in sliced set

    return big


# ---------------------------------------------------------------------------
# select / drop chain (polars)
# ---------------------------------------------------------------------------


def polars_pipeline(path: str) -> pl.DataFrame:
    """Polars: select() narrows, drop() removes — checker tracks both."""
    customers = pl.read_csv(path, columns=["customer_id", "name", "region", "tier"])

    # select() — inferred set narrows to {customer_id, name}
    small = customers.select(["customer_id", "name"])
    print(small["customer_id"])  # ✓ OK
    # Accessing small["region"] would error: 'region' not in selected set

    # drop() on the original — inferred set becomes {customer_id, name, region}
    trimmed = customers.drop(["tier"])
    print(trimmed["region"])  # ✓ OK
    # Accessing trimmed["tier"] would error: 'tier' was dropped

    return trimmed


def drop_then_reuse(path: str) -> pd.DataFrame:
    """Accesses a column that was dropped earlier in the chain — mutation tracking.

    mypy and ty see each intermediate variable as ``pd.DataFrame`` and accept
    any ``str`` subscript.  typedframes tracks the drop and reports E001 on the
    stale access.
    """
    orders = pd.read_csv(path, usecols=["order_id", "customer_id", "amount"])
    trimmed = orders.drop(columns=["customer_id"])
    print(trimmed["customer_id"])  # ✗ E001 — 'customer_id' was dropped
    return trimmed
