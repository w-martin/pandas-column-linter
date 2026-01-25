from typing import TypedDict

from pandas import DataFrame


class UserSchema(TypedDict):
    user_id: int
    email: str


def main() -> None:
    # Use load_users style which is explicitly supported by the linter
    def load_users() -> "DataFrame[UserSchema]":
        return DataFrame({"user_id": [1], "email": ["a@b.com"]})

    df = load_users()
    # 'name' column doesn't exist in UserSchema
    print(df["name"])  # DESIRED: Error: Column 'name' does not exist in UserSchema

    # Column name typo
    print(df["emai"])
    # DESIRED: Error: Column 'emai' does not exist in UserSchema
    # (did you mean 'email'?)
