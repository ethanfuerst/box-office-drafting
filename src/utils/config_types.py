from datetime import datetime, timezone
from typing import Any, NotRequired, TypedDict, cast


class ConfigDict(TypedDict):
    '''
    Configuration dictionary for box office drafting dashboard.

    Required Fields:
        year (int): The year of the box office draft (e.g., 2025).
        name (str): Display name for the dashboard (e.g., '2025 Fantasy Box Office Standings').
        sheet_name (str): Name of the Google Sheet to update.
        database_file (str): Filename of the DuckDB database (e.g., 'friends_2025.duckdb').
        update_type (str): Data source type, either 's3' to read from S3 parquet files
            or 'web' to scrape from boxofficemojo.com.
        gspread_credentials_name (str): Environment variable name containing Google Sheets
            service account credentials JSON.

    Optional Fields:
        bucket (str): S3 bucket name for reading parquet files. Required if update_type is 's3'.

        s3_access_key_id_var_name (str): Environment variable name for S3 access key ID.
            Required if update_type is 's3'.

        s3_secret_access_key_var_name (str): Environment variable name for S3 secret
            access key. Required if update_type is 's3'.
    '''

    # Required fields
    year: int
    name: str
    sheet_name: str
    database_file: str
    update_type: str
    gspread_credentials_name: str

    # Optional fields
    s3_access_key_id_var_name: NotRequired[str]
    s3_secret_access_key_var_name: NotRequired[str]
    bucket: NotRequired[str]


def validate_config(config: ConfigDict) -> ConfigDict:
    '''
    Validate configuration dictionary and return typed ConfigDict.

    Checks that all required fields are present and have correct types.
    Raises ValueError with descriptive message if validation fails.

    Args:
        config: Raw configuration dictionary from YAML file.

    Returns:
        ConfigDict: Validated and typed configuration dictionary.

    Raises:
        ValueError: If required fields are missing or have invalid types.
    '''
    required_fields = {
        'year': int,
        'name': str,
        'sheet_name': str,
        'database_file': str,
        'update_type': str,
        'gspread_credentials_name': str,
    }

    missing_fields = []
    type_errors = []

    for field, expected_type in required_fields.items():
        if field not in config:
            missing_fields.append(field)
        else:
            # Use cast to help mypy understand the key access
            field_value = cast(Any, config.get(field))
            if not isinstance(field_value, expected_type):
                actual_type = type(field_value).__name__
                type_errors.append(
                    f'{field}: expected {expected_type.__name__}, got {actual_type}'
                )

    if 'database_file' in config and isinstance(config['database_file'], str):
        if not config['database_file'].endswith('.duckdb'):
            type_errors.append('database_file: must end with .duckdb')

    if 'year' in config and isinstance(config['year'], int):
        current_year = datetime.now(timezone.utc).year
        valid_years = [current_year - 1, current_year]
        if config['year'] not in valid_years:
            type_errors.append(
                f"year: must be {current_year - 1} or {current_year}, got {config['year']}"
            )

    if 'update_type' in config:
        if config['update_type'] not in ('s3', 'web'):
            type_errors.append("update_type: must be 's3' or 'web'")

    if config.get('update_type') == 's3':
        if 'bucket' not in config:
            type_errors.append("bucket: required when update_type is 's3'")
        if 's3_access_key_id_var_name' not in config:
            type_errors.append("s3_access_key_id_var_name: required when update_type is 's3'")
        if 's3_secret_access_key_var_name' not in config:
            type_errors.append("s3_secret_access_key_var_name: required when update_type is 's3'")

    errors = []
    if missing_fields:
        errors.append(f'Missing required fields: {", ".join(missing_fields)}')
    if type_errors:
        errors.append('Type/validation errors: ' + '; '.join(type_errors))

    if errors:
        raise ValueError('Configuration validation failed:\n' + '\n'.join(errors))

    return config
