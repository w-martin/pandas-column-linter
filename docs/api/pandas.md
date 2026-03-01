# pandas

## Recommended: `Annotated` type annotation

For most use cases, annotate with `Annotated[pd.DataFrame, MySchema]` and use native
pandas subscript access. The checker validates all column references at lint time without
any runtime overhead:

```python
from typing import Annotated
import pandas as pd
from typedframes import BaseSchema, Column

class OrderSchema(BaseSchema):
    order_id   = Column(type=int)
    amount     = Column(type=float)
    status     = Column(type=str)

df: Annotated[pd.DataFrame, OrderSchema] = pd.read_csv("orders.csv")
print(df["order_id"])          # ✓ native pandas, validated by checker
print(df[OrderSchema.amount.s])  # ✓ refactor-safe via .s descriptor
```

## `PandasFrame` — runtime enhancement

`PandasFrame` is a `pd.DataFrame` subclass that adds runtime column validation and
descriptor dispatch (`df[Schema.column]`). Use it when you need:

- Regex `ColumnSet` resolution against actual DataFrame columns at runtime
- Descriptor-based subscript access (`df[Schema.column]`) without `.s`

```python
from typedframes.pandas import PandasFrame
from typedframes import BaseSchema, Column, ColumnSet

class SalesSchema(BaseSchema):
    product_id  = Column(type=int)
    region_cols = ColumnSet(members=r"region_\w+", type=float, regex=True)

# Runtime: resolves regex ColumnSet against actual columns
df = PandasFrame.from_schema(pd.read_csv("sales.csv"), SalesSchema)
```

!!! note
    Prefer `Annotated[pd.DataFrame, Schema]` for new code. `PandasFrame` is most useful
    when regex `ColumnSet` patterns need to be resolved against actual data at runtime.

---

::: typedframes.pandas.PandasFrame
