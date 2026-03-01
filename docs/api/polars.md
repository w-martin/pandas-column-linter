# polars

## Recommended: `Annotated` type annotation

For most use cases, annotate with `Annotated[pl.DataFrame, MySchema]` and use native
polars expressions. The checker validates both subscript access and `pl.col()` references
at lint time:

```python
from typing import Annotated
import polars as pl
from typedframes import BaseSchema, Column

class EventSchema(BaseSchema):
    event_id  = Column(type=int)
    user_id   = Column(type=int)
    timestamp = Column(type=str)

df: Annotated[pl.DataFrame, EventSchema] = pl.read_csv("events.csv")

# Native polars — both forms validated by checker
print(df.select(pl.col("event_id")))             # ✓ pl.col() validated
print(df.filter(pl.col("timestamp").is_not_null()))  # ✓ pl.col() in filter
print(df.select(pl.col("typo")))                  # ✗ E001 — 'typo' not in EventSchema

# Descriptor access — refactor-safe polars expressions
df.select(EventSchema.event_id.col, EventSchema.user_id.col)
df.filter(EventSchema.user_id.col > 100)
```

## `PolarsFrame` — runtime enhancement

`PolarsFrame` is a polars `DataFrame` wrapper that adds descriptor dispatch. Use it when
you want `df[Schema.column]` subscript syntax without `.col`:

```python
from typedframes.polars import PolarsFrame
from typedframes import BaseSchema, Column

class EventSchema(BaseSchema):
    event_id = Column(type=int)

df = PolarsFrame.from_schema(pl.read_csv("events.csv"), EventSchema)
df[EventSchema.event_id]  # descriptor dispatch — returns the column series
```

!!! note
    Prefer `Annotated[pl.DataFrame, Schema]` for new code. The checker validates
    `pl.col()` references directly, so descriptor dispatch is optional.

---

::: typedframes.polars.PolarsFrame
