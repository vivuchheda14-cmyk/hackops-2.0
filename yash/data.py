"""
EcoSentinel - Environmental Intelligence & Compliance Management System
Module: Member 2 - Air Quality Data Pipeline (data.py)

Responsibilities:
1. Connect to CPCB / data.gov.in air-quality API using Python requests.
2. Ingest real-time monitoring station readings (PM2.5, PM10, AQI, etc.).
3. Clean, validate, and normalize records into a consistent Pandas DataFrame.
4. Provide fallback sample data when the API or network is unavailable.
5. Provide a plug-and-play contract for AI (Member 3) & Backend (Member 4).
"""

import os
import re
import logging
from datetime import datetime
from typing import Optional

import requests
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Configure basic logging for debugging and audit trail
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("EcoSentinel.data")

# Load environment variables from .env file if available
load_dotenv()

# ==============================================================================
# API CONFIGURATION & PLACEHOLDERS
# ==============================================================================
# The default endpoint queries the National Air Quality Index (NAQI) published
# by CPCB on data.gov.in.
DEFAULT_BASE_URL = os.getenv("DATAGOV_BASE_URL", "https://api.data.gov.in/resource")
DEFAULT_RESOURCE_ID = os.getenv("DATAGOV_RESOURCE_ID", "3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69")
DEFAULT_API_KEY = os.getenv("DATAGOV_API_KEY", "")
API_TIMEOUT = int(os.getenv("API_TIMEOUT_SECONDS", "10"))

# Standard columns expected by downstream modules (AI, Dashboard, DB)
EXPECTED_COLUMNS = ["station", "timestamp", "pollutant", "value", "unit", "aqi"]


def _standardize_pollutant_name(name: str) -> str:
    """
    Normalizes pollutant strings (e.g., 'PM2_5', 'pm25', 'PM 2.5') into canonical forms.
    Unknown pollutants are preserved without being dropped.
    """
    if not isinstance(name, str) or not name.strip():
        return "Unknown"

    cleaned = name.strip()
    norm = re.sub(r"[\s_\-\.]", "", cleaned).upper()

    if norm in ("PM25", "PM2_5", "PM25MICRONS", "PARTICULATE25"):
        return "PM2.5"
    if norm in ("PM10", "PM10MICRONS", "PARTICULATE10"):
        return "PM10"
    if norm in ("NO2", "NITROGENDIOXIDE"):
        return "NO2"
    if norm in ("SO2", "SULPHURDIOXIDE", "SULFURDIOXIDE"):
        return "SO2"
    if norm in ("CO", "CARBONMONOXIDE"):
        return "CO"
    if norm in ("O3", "OZONE"):
        return "O3"
    if norm in ("NH3", "AMMONIA"):
        return "NH3"

    # Return original cleaned name for any other or unknown pollutants
    return cleaned


def generate_sample_air_quality_data() -> pd.DataFrame:
    """
    Generates a realistic fallback dataset for testing and when the API is unreachable.
    Values are representative benchmarks and clearly flagged as synthetic/sample data.
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sample_records = [
        {"station": "Anand Vihar, Delhi - DPCC", "timestamp": now_str, "pollutant": "PM2.5", "value": 142.5, "unit": "ug/m3", "aqi": 318.0},
        {"station": "Anand Vihar, Delhi - DPCC", "timestamp": now_str, "pollutant": "PM10", "value": 268.0, "unit": "ug/m3", "aqi": 318.0},
        {"station": "Anand Vihar, Delhi - DPCC", "timestamp": now_str, "pollutant": "NO2", "value": 45.2, "unit": "ug/m3", "aqi": 318.0},
        {"station": "ITO, Delhi - CPCB", "timestamp": now_str, "pollutant": "PM2.5", "value": 98.4, "unit": "ug/m3", "aqi": 240.0},
        {"station": "ITO, Delhi - CPCB", "timestamp": now_str, "pollutant": "PM10", "value": 182.0, "unit": "ug/m3", "aqi": 240.0},
        {"station": "R K Puram, Delhi - DPCC", "timestamp": now_str, "pollutant": "PM2.5", "value": 115.0, "unit": "ug/m3", "aqi": 285.0},
        {"station": "R K Puram, Delhi - DPCC", "timestamp": now_str, "pollutant": "PM10", "value": 210.0, "unit": "ug/m3", "aqi": 285.0},
        {"station": "Bandra, Mumbai - MPCB", "timestamp": now_str, "pollutant": "PM2.5", "value": 52.0, "unit": "ug/m3", "aqi": 115.0},
        {"station": "Bandra, Mumbai - MPCB", "timestamp": now_str, "pollutant": "PM10", "value": 94.0, "unit": "ug/m3", "aqi": 115.0},
        {"station": "Bandra, Mumbai - MPCB", "timestamp": now_str, "pollutant": "SO2", "value": 14.8, "unit": "ug/m3", "aqi": 115.0},
        {"station": "BTM Layout, Bengaluru - KSPCB", "timestamp": now_str, "pollutant": "PM2.5", "value": 32.5, "unit": "ug/m3", "aqi": 78.0},
        {"station": "BTM Layout, Bengaluru - KSPCB", "timestamp": now_str, "pollutant": "PM10", "value": 64.0, "unit": "ug/m3", "aqi": 78.0},
        {"station": "BTM Layout, Bengaluru - KSPCB", "timestamp": now_str, "pollutant": "CO", "value": 0.8, "unit": "mg/m3", "aqi": 78.0},
        {"station": "Alipore, Kolkata - WBPCB", "timestamp": now_str, "pollutant": "PM2.5", "value": 85.0, "unit": "ug/m3", "aqi": 190.0},
        {"station": "Alipore, Kolkata - WBPCB", "timestamp": now_str, "pollutant": "PM10", "value": 150.0, "unit": "ug/m3", "aqi": 190.0},
    ]
    df = pd.DataFrame(sample_records)
    df.attrs["is_sample"] = True
    return df


def fetch_air_quality_data(
    api_key: Optional[str] = None,
    resource_id: Optional[str] = None,
    base_url: Optional[str] = None,
    limit: int = 1000
) -> pd.DataFrame:
    """
    Fetches raw air-quality observations from the data.gov.in / CPCB API.

    API Parameter Reference:
    - base_url: Base endpoint URL. Defaults to 'https://api.data.gov.in/resource'
    - resource_id: The specific dataset ID on data.gov.in.
    - api_key: Your personal data.gov.in API key.
    - format: 'json'
    - limit: Total records to retrieve per batch.

    Returns:
        pd.DataFrame containing the raw records from the API, or an empty DataFrame
        if the request fails.
    """
    key = api_key if api_key is not None else DEFAULT_API_KEY
    res_id = resource_id if resource_id is not None else DEFAULT_RESOURCE_ID
    url_base = base_url if base_url is not None else DEFAULT_BASE_URL

    if not key or key.strip() == "your_data_gov_in_api_key_here":
        logger.warning("No valid DATAGOV_API_KEY provided in environment or argument.")
        return pd.DataFrame()

    endpoint = f"{url_base.rstrip('/')}/{res_id}"
    params = {
        "api-key": key,
        "format": "json",
        "limit": limit
    }

    try:
        logger.info(f"Connecting to data.gov.in API endpoint: {endpoint} (limit={limit})")
        response = requests.get(endpoint, params=params, timeout=API_TIMEOUT)
        response.raise_for_status()

        data = response.json()
        if not isinstance(data, dict):
            logger.warning("API returned unexpected JSON root type (not a dict).")
            return pd.DataFrame()

        # data.gov.in resource endpoints return data records in the 'records' key
        records = data.get("records", [])
        if not records:
            logger.warning("API response contains no 'records'.")
            return pd.DataFrame()

        df_raw = pd.DataFrame(records)
        df_raw.attrs["is_sample"] = False
        logger.info(f"Successfully fetched {len(df_raw)} records from API.")
        return df_raw

    except requests.exceptions.Timeout:
        logger.error(f"API request timed out after {API_TIMEOUT} seconds.")
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred while querying API: {http_err}")
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Network error occurred while querying API: {req_err}")
    except ValueError as json_err:
        logger.error(f"Failed to decode API JSON response: {json_err}")
    except Exception as exc:
        logger.error(f"Unexpected error in fetch_air_quality_data: {exc}")

    return pd.DataFrame()


def clean_air_quality_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and standardizes raw air quality data according to the contract:
    - Normalizes column names (handles API aliases).
    - Converts pollutant values to numeric types.
    - Removes invalid negative readings (e.g. -999 sensor error codes).
    - Preserves missing values (does NOT impute with zero).
    - Normalizes pollutant identifiers (e.g., PM2_5 -> PM2.5, PM10).
    - Preserves unknown pollutants.
    - Preserves station names and timestamps.
    - Removes duplicate observations.
    - Returns columns: ['station', 'timestamp', 'pollutant', 'value', 'unit', 'aqi']
    """
    # Preserve sample attribute flag if present
    is_sample = getattr(df, "attrs", {}).get("is_sample", False)

    if df is None or df.empty:
        empty_df = pd.DataFrame(columns=EXPECTED_COLUMNS)
        empty_df.attrs["is_sample"] = is_sample
        return empty_df

    cleaned = df.copy()

    # 1. Normalize column names (strip spaces, lowercase)
    cleaned.columns = [str(col).strip().lower() for col in cleaned.columns]

    # 2. Map standard variations seen in data.gov.in / CPCB APIs
    col_mapping = {
        "station_name": "station",
        "monitoring_station": "station",
        "city_station": "station",
        "last_update": "timestamp",
        "date_time": "timestamp",
        "datetime": "timestamp",
        "date": "timestamp",
        "time": "timestamp",
        "pollutant_id": "pollutant",
        "pollutant_name": "pollutant",
        "parameter": "pollutant",
        "pollutant_avg": "value",
        "avg_value": "value",
        "reading": "value",
        "concentration": "value",
        "pollutant_unit": "unit",
        "units": "unit",
        "air_quality_index": "aqi",
        "index_value": "aqi",
    }
    cleaned = cleaned.rename(columns=col_mapping)

    # 3. Ensure required columns exist
    if "station" not in cleaned.columns:
        cleaned["station"] = "Unknown Station"
    if "timestamp" not in cleaned.columns:
        cleaned["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if "pollutant" not in cleaned.columns:
        cleaned["pollutant"] = "Unknown"
    if "value" not in cleaned.columns:
        cleaned["value"] = np.nan
    if "unit" not in cleaned.columns:
        cleaned["unit"] = "ug/m3"
    if "aqi" not in cleaned.columns:
        cleaned["aqi"] = np.nan

    # 4. Normalize pollutant names while preserving unknowns
    cleaned["pollutant"] = cleaned["pollutant"].astype(str).apply(_standardize_pollutant_name)

    # 5. Clean station and unit strings
    cleaned["station"] = cleaned["station"].astype(str).str.strip()
    cleaned["unit"] = cleaned["unit"].astype(str).str.strip().replace({"NA": "ug/m3", "": "ug/m3", "None": "ug/m3"})

    # 6. Convert numeric readings (pollutant value and AQI)
    cleaned["value"] = pd.to_numeric(cleaned["value"], errors="coerce")
    cleaned["aqi"] = pd.to_numeric(cleaned["aqi"], errors="coerce")

    # 7. Remove invalid negative readings (sensor error codes like -999 or -1)
    # Testing specification: "Negative values are removed."
    cleaned = cleaned[~(cleaned["value"] < 0)]
    cleaned.loc[cleaned["aqi"] < 0, "aqi"] = np.nan

    # 8. Note: Missing values (NaN) are preserved as NaN. NEVER replace with 0!

    # 9. Format timestamp to consistent ISO/readable string
    cleaned["timestamp"] = cleaned["timestamp"].astype(str).str.strip()

    # 10. Deduplicate redundant readings
    cleaned = cleaned.drop_duplicates(subset=["station", "timestamp", "pollutant"], keep="last")

    # 11. Select and order final contract columns
    cleaned = cleaned[EXPECTED_COLUMNS].reset_index(drop=True)
    cleaned.attrs["is_sample"] = is_sample

    return cleaned


def get_air_quality_data() -> pd.DataFrame:
    """
    Main entry point for downstream integration.
    1. Attempts to fetch real data from the configured API.
    2. Cleans the data if retrieved.
    3. If API is unconfigured, unreachable, or empty, seamlessly falls back
       to realistic sample data with df.attrs['is_sample'] = True.
    4. Returns a clean, consistent DataFrame complying with the contract.
    """
    raw_df = fetch_air_quality_data()

    if raw_df is not None and not raw_df.empty:
        cleaned_df = clean_air_quality_data(raw_df)
        if not cleaned_df.empty:
            logger.info("Serving cleaned live data from CPCB / data.gov.in API.")
            return cleaned_df

    # Fallback to sample data
    logger.warning("API data unavailable. Falling back to built-in sample air-quality data.")
    sample_df = generate_sample_air_quality_data()
    cleaned_sample = clean_air_quality_data(sample_df)
    cleaned_sample.attrs["is_sample"] = True
    return cleaned_sample


if __name__ == "__main__":
    print("Testing EcoSentinel Data Module...")
    df = get_air_quality_data()
    is_sample = df.attrs.get("is_sample", False)
    print(f"\n[Result] Retrieved {len(df)} records. Is Sample Fallback: {is_sample}")
    print("\n[DataFrame Contract Preview]")
    print(df.head(10).to_string(index=False))

