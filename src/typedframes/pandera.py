"""Pandera integration for typedframes schemas."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pandera as pa

    from .base_schema import BaseSchema


def _map_dtype(python_type: type) -> type | None:
    """Map a Python type to the corresponding pandera-compatible type.

    Args:
        python_type: The Python type from a Column or ColumnSet definition.

    Returns:
        The type to pass to pandera, or None if no type check should be applied.

    """
    if python_type is Any:
        return None
    return python_type


def to_pandera_schema(schema: type[BaseSchema]) -> pa.DataFrameSchema:
    """Convert a typedframes BaseSchema to a pandera DataFrameSchema.

    Maps Column and ColumnSet definitions to pandera Column objects,
    enabling runtime validation using the same schema definitions
    used for static analysis.

    Args:
        schema: A BaseSchema subclass to convert.

    Returns:
        A pandera DataFrameSchema with columns matching the input schema.

    Raises:
        MissingDependencyError: If pandera is not installed.

    Example:
        class UserData(BaseSchema):
            user_id = Column(type=int)
            email = Column(type=str)
            age = Column(type=int, nullable=True)

        pandera_schema = to_pandera_schema(UserData)
        validated_df = pandera_schema.validate(df)

    """
    try:
        import pandera as pa
    except ImportError:
        from .missing_dependency_error import MissingDependencyError

        package = "pandera"
        raise MissingDependencyError(package, "to_pandera_schema") from None

    columns: dict[str, pa.Column] = {}

    for col in schema.columns().values():
        dtype = _map_dtype(col.type)
        columns[col.column_name] = pa.Column(dtype=dtype, nullable=col.nullable)

    for cs in schema.column_sets().values():
        dtype = _map_dtype(cs.type)
        if cs.regex and isinstance(cs.members, list):
            for pattern in cs.members:
                columns[pattern] = pa.Column(dtype=dtype, nullable=False, regex=True)
        elif isinstance(cs.members, list):
            for member in cs.members:
                columns[member] = pa.Column(dtype=dtype, nullable=False)
        else:
            columns[cs.members] = pa.Column(dtype=dtype, nullable=False)

    strict = not schema.allow_extra_columns

    return pa.DataFrameSchema(columns=columns, strict=strict)
