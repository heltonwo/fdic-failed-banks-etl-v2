"""Load transformed FDIC bank failure data into PostgreSQL."""

from typing import Any, cast

import pandas as pd
from sqlalchemy import MetaData, Table, text
from sqlalchemy.dialects.postgresql import insert

from src.db import get_engine


TABLE_NAME = "failed_banks"

EXPECTED_COLUMNS = (
    "bank_name",
    "city",
    "state",
    "cert",
    "acquiring_institution",
    "closing_date",
    "fund",
    "closing_month",
    "closing_year",
    "closing_quarter",
)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS failed_banks (
    bank_name             TEXT,
    city                  TEXT,
    state                 TEXT,
    cert                  BIGINT PRIMARY KEY,
    acquiring_institution TEXT,
    closing_date          TIMESTAMP,
    fund                  BIGINT,
    closing_month         INTEGER,
    closing_year          INTEGER,
    closing_quarter       INTEGER
)
"""


def load_data(df: pd.DataFrame) -> None:
    """Upsert records using the FDIC certificate number as the key."""

    if df.empty:
        raise ValueError("Refusing to load: the DataFrame is empty.")

    missing_columns = set(EXPECTED_COLUMNS) - set(df.columns)
    unexpected_columns = set(df.columns) - set(EXPECTED_COLUMNS)

    if missing_columns or unexpected_columns:
        raise ValueError(
            "DataFrame column mismatch. "
            f"Missing: {sorted(missing_columns)}; "
            f"unexpected: {sorted(unexpected_columns)}"
        )

    if df["cert"].isna().any() or df["cert"].duplicated().any():
        raise ValueError("Invalid data: `cert` must be unique and non-null.")

    records = cast(
        list[dict[str, Any]],
        df.astype(object).where(df.notna(), None).to_dict("records"),
    )

    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text(CREATE_TABLE_SQL))

        table = Table(TABLE_NAME, MetaData(), autoload_with=conn)

        stmt = insert(table)
        stmt = stmt.on_conflict_do_update(
            index_elements=["cert"],
            set_={
                column: stmt.excluded[column]
                for column in EXPECTED_COLUMNS
                if column != "cert"
            },
        )

        conn.execute(stmt, records)

        total = conn.execute(
            text("SELECT COUNT(*) FROM failed_banks")
        ).scalar_one()

    print(f"Upserted {len(records)} rows. Table now has {total} rows.")