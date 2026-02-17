# Instructions

## Package Structure

- `typedframes`: Python schemas, columns, frames + Rust checker (built with maturin)
- Rust source in `rust/`, compiled into `typedframes._rust_checker` extension module
- Optional deps: `typedframes[pandas]`, `typedframes[polars]`, `typedframes[mypy]`
- Import pattern: `from typedframes.pandas import PandasFrame`, `from typedframes.polars import PolarsFrame`

## Test Guidelines
- Name tests `test_should_<expected_behavior>`
- Follow AAA pattern: `# arrange`, `# act`, `# assert` comments
- Use `unittest.TestCase` for all tests
- Unit tests in `tests/unit/`, integration tests in `tests/integration/`
- One test class per file, one class-under-test per test class
- No `if __name__ == "__main__"` blocks
- Minimize `patch` usage - prefer dependency injection

## Code Style
- Type hints on all functions
- 120 char line limit
- Google-style docstrings
- Custom exceptions with descriptive messages

## Lint Ignore Policy
- Never add ignore rules without user approval
- Never skip bandit rules
- Exceptions must be general patterns, not case-by-case

### Agreed Exceptions (pyproject.toml)
- `D203`, `D212`: Conflict with D211/D213
- `COM812`: Conflicts with ruff formatter
- `PT009`, `PT027`: Using unittest.TestCase
- `PLC0415`: Lazy imports for optional dependencies (polars/pandas)
- `ANN401`: Any needed for pandas compatibility and Python protocols
- `tests/*`: `S101` (assert), `SLF001` (private access), `S603`/`S607` (subprocess)
- `tests/fixtures/*`: `T201` (print for test output)
- `examples/*`: `T201` (print), `INP001` (standalone scripts)
- `src/typedframes/cli.py`: `T201` (print for CLI output)

## Commands

- `uv run inv build` - Build Rust checker in `rust/` (if source changed)
- `uv run inv test` - Tests with coverage (auto-builds)
- `uv run inv lint` - All linters
- `uv run inv all` - Full check suite
- In `tasks.py`, don't prefix commands with `uv run` — invoke already runs inside the uv environment

## Git Policy

- Never run git commands (commit, stash, push, checkout, etc.) without explicit user request

## Documentation Policy
- Never add future work, roadmap items, or collaboration suggestions without user approval
- Never add "Contributing" sections or invitations for external contributions
- Check with user before suggesting any planned features or improvements
