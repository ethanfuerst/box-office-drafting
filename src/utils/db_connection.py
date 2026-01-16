import os

from eftoolkit.sql import DuckDB

from src import project_root
from src.utils.config import ConfigDict


def get_duckdb(config_dict: ConfigDict) -> DuckDB:
    '''Create a configured DuckDB instance from a config dictionary.

    Creates an eftoolkit.sql.DuckDB instance with S3/DigitalOcean Spaces
    configuration based on config_dict values.

    Args:
        config_dict: Configuration dictionary containing draft_id and S3 credentials.

    Returns:
        DuckDB: A configured eftoolkit.sql.DuckDB instance

    Example:
        >>> with get_duckdb(config_dict) as db:
        ...     df = db.query('SELECT * FROM my_table')
    '''
    draft_id = config_dict.get('draft_id', '')
    database_path = project_root / 'src' / 'duckdb_databases' / f'{draft_id}.duckdb'

    s3_access_key_id_var_name = config_dict.get('s3_access_key_id_var_name')
    s3_secret_access_key_var_name = config_dict.get('s3_secret_access_key_var_name')

    # Only configure S3 if credential var names are provided
    s3_access_key_id = (
        os.getenv(s3_access_key_id_var_name) if s3_access_key_id_var_name else None
    )
    s3_secret_access_key = (
        os.getenv(s3_secret_access_key_var_name)
        if s3_secret_access_key_var_name
        else None
    )

    return DuckDB(
        database=str(database_path),
        s3_access_key_id=s3_access_key_id,
        s3_secret_access_key=s3_secret_access_key,
        s3_region=os.getenv('S3_REGION'),
        s3_endpoint=os.getenv('S3_ENDPOINT'),
    )
