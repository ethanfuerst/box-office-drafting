import os

from sqlmesh.core.config import (
    Config,
    DuckDBConnectionConfig,
    GatewayConfig,
    ModelDefaultsConfig,
)

from src import project_root
from src.utils.read_config import get_config_dict


def get_sqlmesh_config(config_path: str) -> Config:
    config = get_config_dict(config_path)
    database_file = config.get('database_file')

    # Get S3 credential environment variable names (handle both naming conventions)
    s3_read_access_key_name = config.get('s3_read_access_key_name') or config.get(
        's3_read_access_key_id_var_name'
    )
    s3_read_secret_access_key_name = config.get(
        's3_read_secret_access_key_name'
    ) or config.get('s3_read_secret_access_key_var_name')

    # Build secrets list only if S3 credentials are configured
    secrets = []
    if s3_read_access_key_name and s3_read_secret_access_key_name:
        key_id = os.getenv(s3_read_access_key_name)
        secret = os.getenv(s3_read_secret_access_key_name)
        if key_id and secret:
            secrets = [
                {
                    'type': 'S3',
                    'region': 'nyc3',
                    'endpoint': 'nyc3.digitaloceanspaces.com',
                    'key_id': key_id,
                    'secret': secret,
                },
            ]

    return Config(
        model_defaults=ModelDefaultsConfig(dialect='duckdb'),
        gateways={
            'duckdb': GatewayConfig(
                connection=DuckDBConnectionConfig(
                    database=str(
                        project_root / 'src' / 'duckdb_databases' / database_file
                    ),
                    extensions=[
                        {'name': 'httpfs'},
                    ],
                    secrets=secrets,
                )
            )
        },
        variables={
            'year': config.get('year'),
            'update_type': config.get('update_type'),
            'bucket': config.get('bucket'),
            'sheet_name': config.get('sheet_name'),
            'gspread_credentials_name': config.get('gspread_credentials_name'),
        },
    )


config = get_sqlmesh_config(os.getenv('CONFIG_PATH'))
