# Developing typedframes

## Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) - Python package manager
- Rust toolchain (for building the linter extension)

## Setup

1. Clone the repository:

```shell
git clone https://github.com/w-martin/typedframes.git
cd typedframes
```

2. Install dependencies and build the Rust extension:

```shell
uv sync
uv run maturin develop
```

3. Install pre-commit hooks:

```shell
uv run pre-commit install
```

## Task Commands

All development tasks are managed via [Invoke](https://www.pyinvoke.org/). Run `uv run inv --list` to see available tasks.

### Format Code

```shell
uv run inv format
```

Runs `ruff format` on the entire codebase.

### Lint Code

```shell
uv run inv lint
```

Runs all linters:
- `ruff check` - Python linting
- `ty check` - Type checking
- `bandit` - Security linting
- `complexipy` - Complexity checking (max complexity: 8)

### Fix Linting Issues

```shell
uv run inv lint-fix
```

Runs `ruff check --fix` and `ruff format` to auto-fix issues.

### Run Tests

```shell
uv run inv test
```

Runs pytest with branch coverage. Coverage must be 100% or the build fails.

### Verify Licenses

```shell
uv run licensecheck
```

Runs licensecheck to verify all dependency licenses are compatible.

### Run All Checks

```shell
uv run inv all
```

Runs all checks in order: format, lint, test, verify-licences.

## Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`:

- Trailing whitespace removal
- End-of-file fixer
- YAML syntax check
- Large file check
- Ruff linting with auto-fix
- Ruff formatting

To run hooks manually on all files:

```shell
uv run pre-commit run --all-files
```

## Coverage Requirements

This project requires 100% branch coverage. The coverage configuration excludes:
- `TYPE_CHECKING` blocks
- `raise NotImplementedError` statements
- Lines marked with `# pragma: no cover`

## Building the Rust Linter

The Rust linter extension is built with maturin:

```shell
uv run maturin develop
```

For release builds:

```shell
uv run maturin build --release
```
