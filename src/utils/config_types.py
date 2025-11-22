from typing import NotRequired, TypedDict


class ConfigDict(TypedDict):
    '''
    Configuration dictionary for box office drafting dashboard.

    Required Fields:
        year (int): The year of the box office draft (e.g., 2025).
        name (str): Display name for the dashboard (e.g., '2025 Fantasy Box Office Standings').
        sheet_name (str): Name of the Google Sheet to update.
        database_file (str): Filename of the DuckDB database (e.g., 'friends_2025.duckdb').

    Optional Fields:
        gspread_credentials_name (str): Environment variable name containing Google Sheets
            service account credentials JSON. Defaults to 'GSPREAD_CREDENTIALS_{year}' if not provided.

        update_type (str): Data source type, either 's3' to read from S3 parquet files
            or 'web' to scrape from boxofficemojo.com. Defaults to 's3'.

        bucket (str): S3 bucket name for reading parquet files. Required if update_type is 's3'.

        s3_read_access_key_id_var_name (str): Environment variable name for S3 read access key ID.
            Defaults to 'S3_ACCESS_KEY_ID' if not provided.

        s3_read_secret_access_key_var_name (str): Environment variable name for S3 read secret
            access key. Defaults to 'S3_SECRET_ACCESS_KEY' if not provided.

        s3_read_access_key_name (str): Alternative name for S3 read access key ID env var.
            Used for backward compatibility.

        s3_read_secret_access_key_name (str): Alternative name for S3 read secret access key
            env var. Used for backward compatibility.

        s3_write_access_key_id_var_name (str): Environment variable name for S3 write access
            key ID. Only needed if write access to S3 is required.

        s3_write_secret_access_key_var_name (str): Environment variable name for S3 write
            secret access key. Only needed if write access to S3 is required.
    '''

    # Required fields
    year: int
    name: str
    sheet_name: str
    database_file: str

    # Optional fields
    gspread_credentials_name: NotRequired[str]
    s3_read_access_key_name: NotRequired[str]
    s3_read_access_key_id_var_name: NotRequired[str]
    s3_read_secret_access_key_name: NotRequired[str]
    s3_read_secret_access_key_var_name: NotRequired[str]
    s3_write_access_key_id_var_name: NotRequired[str]
    s3_write_secret_access_key_var_name: NotRequired[str]
    update_type: NotRequired[str]
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
    }

    missing_fields = []
    type_errors = []

    for field, expected_type in required_fields.items():
        if field not in config:
            missing_fields.append(field)
        elif not isinstance(config[field], expected_type):
            actual_type = type(config[field]).__name__
            type_errors.append(
                f'{field}: expected {expected_type.__name__}, got {actual_type}'
            )

    if 'database_file' in config and isinstance(config['database_file'], str):
        if not config['database_file'].endswith('.duckdb'):
            type_errors.append('database_file: must end with .duckdb')

    if 'update_type' in config and config['update_type'] is not None:
        if config['update_type'] not in ('s3', 'web'):
            type_errors.append("update_type: must be 's3' or 'web'")

    if config.get('update_type') == 's3' and 'bucket' not in config:
        type_errors.append("bucket: required when update_type is 's3'")

    errors = []
    if missing_fields:
        errors.append(f'Missing required fields: {", ".join(missing_fields)}')
    if type_errors:
        errors.append('Type/validation errors: ' + '; '.join(type_errors))

    if errors:
        raise ValueError('Configuration validation failed:\n' + '\n'.join(errors))

    return config
