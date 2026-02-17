from typing import cast

import polars as pl

from typedframes import BaseSchema, Column
from typedframes.polars import PolarsFrame


class UserSchema(BaseSchema):
    user_id = Column(type=int)
    email = Column(type=str)


def main() -> None:
    def load_users() -> PolarsFrame[UserSchema]:
        return cast("PolarsFrame[UserSchema]", pl.DataFrame({"user_id": [1], "email": ["a@b.com"]}))

    df = load_users()
    # 'name' column doesn't exist in UserSchema
    print(df.select(UserSchema.email.col))
    print(df.select(UserSchema.user_id.col))
    print(df["name"])  # DESIRED: Error: Column 'name' does not exist in UserSchema

    # Column name typo
    print(df["emai"])
    # DESIRED: Error: Column 'emai' does not exist in UserSchema
    # (did you mean 'email'?)


if __name__ == "__main__":
    main()
