"""Extract step: downloads the FDIC bank failures CSV."""

from io import BytesIO

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

URL = "https://fdic.gov/bank-failures/download-data.csv"


def extract_fdic_data() -> pd.DataFrame:
    """Download the FDIC bank failures CSV into a DataFrame."""

    print("Downloading FDIC data...")

    retry_strategy = Retry(
        total=3,
        connect=3,
        read=3,
        status=3,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)

    try:
        with requests.Session() as session:
            session.mount("https://", adapter)

            response = session.get(URL, timeout=(5, 30))
            response.raise_for_status()

            df = pd.read_csv(
                BytesIO(response.content),
                encoding="ISO-8859-1",
            )

    except requests.RequestException as exc:
        raise RuntimeError(
            f"Failed to download FDIC data from {URL}: {exc}"
        ) from exc

    print(f"Data loaded successfully! Total rows: {len(df)}")
    return df


if __name__ == "__main__":
    extract_fdic_data()
