"""Sentinel class for deferred column definitions."""


class DefinedLater:
    """
    Sentinel class indicating a value will be defined at runtime.

    Use the class itself (not an instance) as a marker for Column aliases
    or ColumnSet members that will be provided later, typically during runtime.

    If any read operation is attempted before the placeholder is replaced with
    the actual value, a ColumnAliasNotYetDefinedException or
    ColumnSetMembersNotYetDefinedException will be raised.

    Example:
        class DynamicSchema(BaseSchema):
            data = Column(type=str, alias=DefinedLater)  # Alias set at runtime

    """
