"""Transform step: validates, cleans and enriches FDIC bank failure data."""

import pandas as pd


REQUIRED_COLUMNS = {
    "bank_name",
    "city",
    "state",
    "cert",
    "acquiring_institution",
    "closing_date",
    "fund",
}


def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean FDIC data and derive closing month, year and quarter."""

    print("Starting data transformation...")

    if df.empty:
        raise ValueError("Transformation failed: the source DataFrame is empty.")

    df_clean = df.copy()

    # Normalize ordinary spaces and non-breaking spaces in column names.
    df_clean.columns = (
        df_clean.columns
        .str.replace("\u00a0", " ", regex=False)
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", "_", regex=True)
    )

    missing_columns = REQUIRED_COLUMNS - set(df_clean.columns)

    if missing_columns:
        raise ValueError(
            "Transformation failed: missing required columns: "
            f"{sorted(missing_columns)}"
        )

    # Preserve missing dates while identifying malformed, non-empty values.
    original_dates = df_clean["closing_date"]
    parsed_dates = pd.to_datetime(
        original_dates,
        format="%d-%b-%y",
        errors="coerce",
    )

    invalid_dates = original_dates.notna() & parsed_dates.isna()
    invalid_count = int(invalid_dates.sum())
    missing_count = int(original_dates.isna().sum())

    df_clean["closing_date"] = parsed_dates

    if invalid_count:
        print(f"Warning: {invalid_count} invalid closing date(s) converted to NaT.")

    if missing_count:
        print(f"Notice: {missing_count} source record(s) have no closing date.")

    df_clean["closing_month"] = df_clean["closing_date"].dt.month
    df_clean["closing_year"] = df_clean["closing_date"].dt.year
    df_clean["closing_quarter"] = df_clean["closing_date"].dt.quarter

    print("\nShape:")
    print(df_clean.shape)

    print("\nColumns:")
    print(df_clean.columns.tolist())

    print("\nData types:")
    print(df_clean.dtypes)

    print("\nFirst rows:")
    print(df_clean.head())

    return df_clean


if __name__ == "__main__":
    from src.extract import extract_fdic_data

    raw_df = extract_fdic_data()
    transform_data(raw_df)
