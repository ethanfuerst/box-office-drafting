import os
from pathlib import Path

from sqlmesh.core.config import (
    Config,
    DuckDBConnectionConfig,
    GatewayConfig,
    ModelDefaultsConfig,
)

from src import project_root
from src.utils.config_types import ConfigDict
from src.utils.constants import (
    DUCKDB_EXTENSION_HTTPFS,
    S3_ENDPOINT,
    S3_REGION,
    S3_SECRET_TYPE,
)
from src.utils.read_config import get_config_dict


def get_sqlmesh_config(config_path: Path | str) -> Config:
    config: ConfigDict = get_config_dict(config_path)
    database_file = config.get('database_file')

    s3_access_key_id_var_name = config.get('s3_access_key_id_var_name')
    s3_secret_access_key_var_name = config.get('s3_secret_access_key_var_name')

    # Build secrets list only if S3 credentials are configured
    secrets = []
    key_id = os.getenv(s3_access_key_id_var_name)
    secret = os.getenv(s3_secret_access_key_var_name)
    if key_id and secret:
        secrets = [
            {
                'type': S3_SECRET_TYPE,
                'region': S3_REGION,
                'endpoint': S3_ENDPOINT,
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
                        {'name': DUCKDB_EXTENSION_HTTPFS},
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
