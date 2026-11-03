"""
EcoSentinel Unit Test Suite
Verifies Member 2 Data Pipeline and Contract Compliance:
- Expected columns in DataFrame
- PM2.5 and PM10 normalization
- Negative values removal
- Missing values preserved (not converted to zero)
- Unknown pollutants preserved
- API failure fallback handling
- Empty DataFrame resilience
"""

import sys
import os
import unittest
import numpy as np
import pandas as pd

# Ensure EcoSentinel module path is loaded
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data import (
    clean_air_quality_data,
    get_air_quality_data,
    fetch_air_quality_data,
    EXPECTED_COLUMNS
)


class TestAirQualityPipeline(unittest.TestCase):

    def test_expected_columns(self):
        """Verify the cleaned DataFrame adheres strictly to the required contract schema."""
        df = get_air_quality_data()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertListEqual(list(df.columns), EXPECTED_COLUMNS)

    def test_pm25_and_pm10_extracted_and_normalized(self):
        """Verify pollutant aliases (e.g. 'PM2_5', 'pm25', 'pm 10') are mapped to PM2.5 and PM10."""
        raw_mock = pd.DataFrame([
            {"station": "Station Alpha", "last_update": "2026-11-03 10:00", "pollutant_id": "PM2_5", "pollutant_avg": "45.0", "aqi": "110"},
            {"station": "Station Alpha", "last_update": "2026-11-03 10:00", "pollutant_id": "pm25", "pollutant_avg": "55.0", "aqi": "110"},
            {"station": "Station Alpha", "last_update": "2026-11-03 10:00", "pollutant_id": "pm 10", "pollutant_avg": "90.0", "aqi": "110"},
        ])
        cleaned = clean_air_quality_data(raw_mock)
        pollutants = set(cleaned["pollutant"].unique())
        self.assertIn("PM2.5", pollutants)
        self.assertIn("PM10", pollutants)

    def test_negative_values_removed(self):
        """Verify sensor error negative values (e.g., -999, -5.0) are removed."""
        raw_mock = pd.DataFrame([
            {"station": "Station Beta", "timestamp": "2026-11-03 10:00", "pollutant": "PM2.5", "value": -999.0, "unit": "ug/m3", "aqi": 50},
            {"station": "Station Beta", "timestamp": "2026-11-03 10:00", "pollutant": "PM10", "value": 75.0, "unit": "ug/m3", "aqi": 50},
        ])
        cleaned = clean_air_quality_data(raw_mock)
        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned.iloc[0]["pollutant"], "PM10")
        self.assertFalse((cleaned["value"] < 0).any())

    def test_missing_values_not_converted_to_zero(self):
        """Verify missing/null pollutant values remain NaN and are NOT replaced with 0."""
        raw_mock = pd.DataFrame([
            {"station": "Station Gamma", "timestamp": "2026-11-03 10:00", "pollutant": "PM2.5", "value": None, "unit": "ug/m3", "aqi": None},
            {"station": "Station Gamma", "timestamp": "2026-11-03 10:00", "pollutant": "PM10", "value": np.nan, "unit": "ug/m3", "aqi": np.nan},
        ])
        cleaned = clean_air_quality_data(raw_mock)
        self.assertEqual(len(cleaned), 2)
        # Verify values remain NaN, never converted to 0.0
        self.assertTrue(cleaned["value"].isna().all())
        self.assertFalse((cleaned["value"] == 0).any())
        self.assertTrue(cleaned["aqi"].isna().all())

    def test_unknown_pollutants_preserved(self):
        """Verify atypical or new pollutants (e.g. Formaldehyde, VOC) are preserved rather than dropped."""
        raw_mock = pd.DataFrame([
            {"station": "Station Delta", "timestamp": "2026-11-03 10:00", "pollutant": "Formaldehyde", "value": 12.4, "unit": "ug/m3", "aqi": 40},
            {"station": "Station Delta", "timestamp": "2026-11-03 10:00", "pollutant": "VOC_Total", "value": 3.8, "unit": "ppm", "aqi": 40},
        ])
        cleaned = clean_air_quality_data(raw_mock)
        self.assertIn("Formaldehyde", cleaned["pollutant"].values)
        self.assertIn("VOC_Total", cleaned["pollutant"].values)

    def test_api_failure_fallback_handling(self):
        """Verify that an invalid API key or unreachable server triggers the sample data fallback gracefully."""
        # Using a dummy invalid key to simulate API error
        df = fetch_air_quality_data(api_key="invalid_test_key", base_url="https://invalid.domain.xyz")
        self.assertTrue(df.empty)

        # get_air_quality_data should cleanly fall back to sample dataset with is_sample=True
        fallback_df = get_air_quality_data()
        self.assertFalse(fallback_df.empty)
        self.assertTrue(fallback_df.attrs.get("is_sample", False))

    def test_empty_dataframe_handling(self):
        """Verify clean_air_quality_data handles None and empty DataFrames without crashing."""
        empty_cleaned = clean_air_quality_data(pd.DataFrame())
        self.assertIsInstance(empty_cleaned, pd.DataFrame)
        self.assertListEqual(list(empty_cleaned.columns), EXPECTED_COLUMNS)
        self.assertEqual(len(empty_cleaned), 0)

        none_cleaned = clean_air_quality_data(None)
        self.assertIsInstance(none_cleaned, pd.DataFrame)
        self.assertListEqual(list(none_cleaned.columns), EXPECTED_COLUMNS)
        self.assertEqual(len(none_cleaned), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

