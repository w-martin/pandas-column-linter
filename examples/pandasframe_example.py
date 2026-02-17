import pandas as pd

from typedframes import BaseSchema, Column
from typedframes.pandas import PandasFrame


class UserSchema(BaseSchema):
    user_id = Column(type=int)
    email = Column(type=str)


def main() -> None:
    def load_users() -> PandasFrame[UserSchema]:
        return PandasFrame.from_schema(pd.DataFrame({"user_id": [1], "email": ["a@b.com"]}), UserSchema)

    df = load_users()
    # 'name' column doesn't exist in UserSchema
    print(df[UserSchema.email])
    print(df[UserSchema.user_id])
    print(df["name"])  # DESIRED: Error: Column 'name' does not exist in UserSchema

    # Column name typo
    print(df["emai"])
    # DESIRED: Error: Column 'emai' does not exist in UserSchema
    # (did you mean 'email'?)


if __name__ == "__main__":
    main()
