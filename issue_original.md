# Feature Request: Static Analysis for DataFrame Column Schemas

## Problem Statement

Python ML/data science projects using pandas/polars lack static analysis for DataFrame column schemas. This leads to runtime errors from column mismatches that could be caught at lint-time.

**Current situation:**
- `pandas-stubs` provides API types but no column-level tracking
- `pandera` adds static analysis via mypy plugin but misses cases due to DataFrame mutability handling

No tool catches this error statically:
```python
# example.py
# Highlights lint checks missing with mypy/pandera

import pandera as pa
from pandera.typing import DataFrame, Series


class UserSchema(pa.DataFrameModel):
    """Schema defining user data structure"""

    user_id: Series[int]
    email: Series[str]


class OrderSchema(pa.DataFrameModel):
    """Schema defining order data structure"""

    order_id: Series[int]
    amount: Series[float]


def load_users() -> DataFrame[UserSchema]:
    return DataFrame[UserSchema](  # must instantiate pandera DataFrame with schema
        {"user_id": ["foo", "bar"], "email": ["foo@baz.com", "bar@qux.com"]},
    )


def process_orders(df: DataFrame[OrderSchema]) -> None:
    """Process orders - expects OrderSchema"""
    # This should work
    print(df["order_id"].sum())
    print(df["amount"].mean())


def main() -> None:
    # Passing wrong schema to function
    # We load users (UserSchema) but pass to function expecting orders (OrderSchema)
    users = load_users()
    process_orders(users)  # mypy catches this as DataFrame type mismatch, but NOT because of column schemas

    # Issue 1: Accessing non-existent column
    users = load_users()
    # 'name' column doesn't exist in UserSchema
    print(users["name"])  # mypy SHOULD error here but doesn't

    # Issue 2: Mutation breaks tracking
    users = load_users()  # Has UserSchema
    users["new_column"] = 123  # Now has extra column
    # mypy has no idea about the mutation

    # Issue 3: Column name typo
    users = load_users()
    print(users["emai"])  # Typo: 'emai' instead of 'email' - not caught


if __name__ == "__main__":
    main()

# All 3 issues are NOT caught by static analysis.
# Pandera only validates at runtime when you explicitly call .validate()
# or use @pa.check_types decorator (which is runtime checking, not static)
#
## Expected Behavior
#
#    Running `ty check example.py` should report:
#    - Line X: Column 'name' does not exist in UserSchema
#    - Line Y: Column 'emai' does not exist in UserSchema (did you mean 'email'?)
#    - Mutation tracking: Warning about untracked schema changes
```

## Proposed Solution

Enable `ty` to understand DataFrame column schemas through either:

1. **Plugin/Extension API** that allows domain-specific type checking
2. **Built-in support** for `DataFrame[SchemaType]` generic syntax
3. **Advanced stub interpretation** that encodes column information

**Desired syntax:**
```python
from pandas import DataFrame
from typing import TypedDict

class UserSchema(TypedDict):
    user_id: int
    email: str

def load_users() -> DataFrame[UserSchema]:
    ...

def process(df: DataFrame[UserSchema]) -> None:
    df['name']  # ty error: Column 'name' not in UserSchema
    df['user_id']  # OK
```

## Why This Matters

- **Impact:** Affects every data science/ML team using Python
- **Current pain:** Bugs only caught through extensive testing, takes time to dig into where the issue is introduced
- **Performance:** Static checking is orders of magnitude faster than runtime validation
- **ty's strength:** Rust-based speed makes this practical for large codebases

## Implementation Considerations

**Option A: Plugin System**
- Mypy has a plugin API (`mypy.plugin`) that pandera attempted to use
- A ty plugin API could enable this and many other domain-specific analyses
- Could benefit entire ecosystem (SQLAlchemy, Pydantic, etc.)

**Option B: Direct Integration**
- DataFrame column tracking could be built into ty's core
- Rust implementation would be extremely fast
- Could become a killer feature for ty

**Option C: Enhanced Stub Support**
- If stubs could express "this DataFrame has these columns"
- ty's existing generic type support might be sufficient?
- Lowest barrier to entry

## I Can Help

I'm willing to:
- Contribute to design discussions
- Help implement this feature (Rust novice)
- Test and provide feedback
- Document for the community

## Context

I work on ML infrastructure and have experience with:
- Pandas/numpy codebases at scale
- Previously built `pandandic` for DataFrame validation
- Familiar with type checking concepts, new to ty internals

---

**Is a plugin system on ty's roadmap? Would you be open to collaboration on this feature? Thanks!**
