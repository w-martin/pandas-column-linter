# typedframes: Static Analysis for DataFrame Column Schemas

## Overview

typedframes provides static analysis for pandas and polars DataFrames, catching column access errors at lint-time rather than runtime.

## Features

### 1. Missing Column Detection

```python
from typing import Annotated
import polars as pl
from typedframes import BaseSchema, Column

class UserSchema(BaseSchema):
    user_id = Column(type=int)
    email = Column(type=str)

df: Annotated[pl.DataFrame, UserSchema] = pl.DataFrame({...})
print(df["name"])  # Error: Column 'name' does not exist in UserSchema
```

### 2. Typo Correction Suggestions

```python
print(df["emai"])  # Error: Column 'emai' does not exist (did you mean 'email'?)
```

### 3. Mutation Tracking

```python
df["new_column"] = 123  # Warning: Column 'new_column' does not exist (mutation tracking)
```

## How It Works

typedframes consists of three components:

1. **Python Schema Definitions** (`src/typedframes/`)
   - `BaseSchema`: Define DataFrame column schemas
   - `Column`: Single column definition with type and optional alias
   - `ColumnSet`: Pattern-matched column groups (regex support)
   - `PandasFrame`: pandas DataFrame subclass with schema-aware attribute access
   - `PolarsFrame`: Type alias for annotated polars DataFrames

2. **Rust Linter** (`rust_typedframes_linter/`)
   - Parses Python files using tree-sitter
   - Extracts schema definitions from `BaseSchema` subclasses
   - Tracks DataFrame variables with schema type annotations
   - Detects invalid column accesses via subscript operations
   - Uses Levenshtein distance for typo suggestions

3. **Mypy Plugin** (`src/typedframes/mypy.py`)
   - Integrates the Rust linter with mypy
   - Hooks into DataFrame `__getitem__` and `__setitem__` calls
   - Reports linter errors as mypy diagnostics

## Usage

### Installation

```bash
uv add typedframes
```

### Define Schemas

```python
from typedframes import BaseSchema, Column, ColumnSet

class UserSchema(BaseSchema):
    user_id = Column(type=int)
    email = Column(type=str, alias="email_address")
    scores = ColumnSet(members=r"score_\d+", type=float, regex=True)
```

### Use with Polars (Recommended)

```python
from typing import Annotated
import polars as pl

df: Annotated[pl.DataFrame, UserSchema] = pl.read_csv("users.csv")

# Schema-based column references
df.filter(UserSchema.user_id.col > 10)
df.select(UserSchema.email.col, UserSchema.user_id.col)
```

### Use with Pandas

```python
from typedframes import PandasFrame
import pandas as pd

df = PandasFrame.from_schema(pd.read_csv("users.csv"), UserSchema)

# Access columns by schema attribute name
df.user_id  # Returns the user_id column
df.email    # Returns email_address column (via alias)
```

### Enable Mypy Plugin

Add to `pyproject.toml`:

```toml
[tool.mypy]
mypy_path = "src"
plugins = ["typedframes.mypy"]
```

Then run mypy:

```bash
mypy your_code.py
```

### Run Rust Linter Directly

```bash
typedframes_linter your_code.py
```

Output is JSON:
```json
[{"line": 10, "col": 7, "message": "Column 'foo' does not exist in UserSchema"}]
```

## Configuration

In `pyproject.toml`:

```toml
[tool.typedframes]
enabled = true  # Enable/disable the linter (default: true)
```

## Limitations

- Schema type annotations must use `Annotated[pl.DataFrame, Schema]` or `PandasFrame[Schema]`
- Forward references (string annotations) are not fully supported
- Dynamic schema modifications at runtime are not tracked

## Development

See [DEVELOPING.md](DEVELOPING.md) for development setup and contribution guidelines.
