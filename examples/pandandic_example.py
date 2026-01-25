from pandandic import BaseFrame, Column, ColumnSet


class UserFrame(BaseFrame):
    user_id = Column(type=int)
    email = Column(type=str, alias="email_address")
    metadata = ColumnSet(members=["age", "gender"])


def main() -> None:
    # Use from_df for example purposes
    import pandas as pd

    UserFrame().from_df(
        pd.DataFrame(
            {
                "user_id": [1],
                "email_address": ["a@b.com"],
                "age": [20],
                "gender": ["m"],
            },
        ),
    )

    # Typo detection on attribute
    # DESIRED: Error: Column 'emai' does not exist in UserFrame
    # (did you mean 'email_address'?)
