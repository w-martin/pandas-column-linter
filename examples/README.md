# Examples

## multi_file_inference/

Demonstrates aggressive column inference across multiple files **without any
`BaseSchema` classes**.  The checker infers column sets from `usecols=` /
`columns=` / `dtype=` arguments and propagates them through method chains
(rename, drop, assign, select, filter).

The directory contains two intentional errors — a wrong column name after
`usecols=` and an access on a column that was dropped earlier in the chain.
Both are invisible to mypy and ty because `df["any_string"]` is a valid
subscript on `pd.DataFrame` / `pl.DataFrame` from their perspective.

```shell
uv run mypy --config-file mypy_empty.ini multi_file_inference/
```
```shell
uv run ty check multi_file_inference/
```
```shell
uv run typedframes check multi_file_inference/
```

## multi_file_with_schema/

Same multi-file scenario, but `BaseSchema` classes carry the column set across
module boundaries.  Functions annotated `-> PandasFrame[Schema]` are indexed by
the checker; call sites in other files are validated against that schema without
needing `usecols=` or local annotations.

The directory contains two intentional errors in `pipeline.py` that access
columns absent from `OrderSchema`.  The schema is defined in `schemas.py` and
the returning function in `loaders.py` — the errors are only detectable by
tracing across all three files.  mypy and ty accept the calls because
`PandasFrame.__getitem__` takes a `str` and returns `Any`.

```shell
uv run mypy --config-file mypy_empty.ini multi_file_with_schema/
```

```shell
uv run ty check multi_file_with_schema/
```

```shell
uv run typedframes check multi_file_with_schema/
```

## inference_example.py

```shell
uv run mypy --config-file mypy_empty.ini --strict inference_example.py
```

```shell
uv run ty check inference_example.py
```

```shell
uv run typedframes check inference_example.py
```

## pandasframe_example.py

```shell
uv run mypy --config-file mypy_empty.ini --strict pandasframe_example.py
```

```shell
uv run ty check pandasframe_example.py
```

```shell
uv run typedframes check pandasframe_example.py
```

## pandera_example.py

```shell
uv run mypy --config-file mypy_empty.ini --strict pandera_example.py
```

```shell
uv run ty check pandera_example.py
```

```shell
uv run typedframes check pandera_example.py
```

## polarsframe_example.py

```shell
uv run mypy --config-file mypy_empty.ini --strict polarsframe_example.py
```

```shell
uv run ty check polarsframe_example.py
```

```shell
uv run typedframes check polarsframe_example.py
```

## schema_algebra_example.py

```shell
uv run mypy --config-file mypy_empty.ini --strict schema_algebra_example.py
```

```shell
uv run ty check schema_algebra_example.py
```

```shell
uv run typedframes check schema_algebra_example.py
```

## typedframes_example.py

```shell
uv run mypy --config-file mypy_empty.ini --strict typedframes_example.py
```

```shell
uv run ty check typedframes_example.py
```

```shell
uv run typedframes check typedframes_example.py
```
