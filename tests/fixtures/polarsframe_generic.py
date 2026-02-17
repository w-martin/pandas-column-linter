"""Test fixture: PolarsFrame used with type arguments."""

import polars as pl

from typedframes import BaseSchema, Column
from typedframes.polars import PolarsFrame


class UserSchema(BaseSchema):
    """Test schema for user data."""

    user_id = Column(type=int)
    email = Column(type=str)


df: PolarsFrame[UserSchema] = pl.DataFrame(
    {
        "user_id": [1, 2],
        "email": ["a@b.com", "c@d.com"],
    }
)
