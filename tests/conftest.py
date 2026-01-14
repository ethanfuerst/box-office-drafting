"""Shared fixtures for box office drafting tests."""

from datetime import datetime, timezone

import pandas as pd
import pytest


def make_sample_dataframe(rows: int = 5, columns: list[str] | None = None) -> pd.DataFrame:
    """Create a sample DataFrame for testing.

    Args:
        rows: Number of rows to generate.
        columns: Column names. Defaults to ['A', 'B', 'C'].

    Returns:
        A DataFrame with sequential integer values.
    """
    if columns is None:
        columns = ['A', 'B', 'C']
    data = {col: list(range(rows)) for col in columns}
    return pd.DataFrame(data)


def make_config_dict(
    year: int | None = None,
    update_type: str = 'web',
    include_s3_fields: bool = False,
) -> dict:
    """Create a minimal valid config dict for testing.

    Args:
        year: The year for the config. Defaults to current year.
        update_type: Either 's3' or 'web'.
        include_s3_fields: Whether to include S3-related fields.

    Returns:
        A dictionary matching ConfigDict structure.
    """
    if year is None:
        year = datetime.now(timezone.utc).year

    config = {
        'year': year,
        'name': 'Test Draft',
        'sheet_name': 'Test Sheet',
        'draft_id': 'test_draft',
        'update_type': update_type,
        'gspread_credentials_name': 'TEST_GSPREAD_CREDS',
    }

    if include_s3_fields or update_type == 's3':
        config.update({
            'bucket': 'test-bucket',
            's3_access_key_id_var_name': 'TEST_S3_KEY_ID',
            's3_secret_access_key_var_name': 'TEST_S3_SECRET',
        })

    return config


@pytest.fixture
def current_year() -> int:
    """Return the current UTC year."""
    return datetime.now(timezone.utc).year
