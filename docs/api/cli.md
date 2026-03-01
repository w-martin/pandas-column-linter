# CLI

The `typedframes` command-line interface runs the Rust-based static checker on Python source files.

## Basic usage

```shell
# Check a single file
typedframes check pipeline.py

# Check an entire directory (builds a cross-file project index)
typedframes check src/

# Check without building the project index (each file checked independently)
typedframes check src/ --no-index

# Enable W001 warnings for bare DataFrame loads (off by default)
typedframes check src/ --strict-ingest
```

## Output format

```
src/pipeline.py:42 - E001: Column 'revenue' not in OrderSchema
src/pipeline.py:57 - E002: Column 'user_id' renamed to 'customer_id', use 'customer_id'
```

## Error codes

| Code | Meaning | Default |
|------|---------|---------|
| E001 | Column not found in schema or inferred set | Always shown |
| E002 | Column was renamed — use the new name | Always shown |
| W001 | Bare DataFrame load — no column info for checker | Off (use `--strict-ingest`) |
| W002 | Column access on untracked DataFrame | Off (use `--strict-ingest`) |

## Project-level configuration

Add to `pyproject.toml` to disable all warnings project-wide:

```toml
[tool.typedframes]
enabled  = true
warnings = false
```

---

::: typedframes.cli.main
