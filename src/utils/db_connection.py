import os
from contextlib import contextmanager
from typing import Any, Iterator

import duckdb
from dotenv import load_dotenv

from src import project_root
from src.utils.config import ConfigDict
from src.utils.constants import (
    DUCKDB_EXTENSION_HTTPFS,
    S3_ENDPOINT,
    S3_REGION,
    S3_SECRET_TYPE,
)

load_dotenv()


class DuckDBConnection:
    def __init__(self, config_dict: ConfigDict, need_write_access: bool = False) -> None:
        '''Initialize a DuckDB connection with S3 configuration.'''
        draft_id = config_dict.get('draft_id', '')
        database_name = (
            project_root / 'src' / 'duckdb_databases' / f'{draft_id}.duckdb'
        )

        self.connection = duckdb.connect(
            database=str(database_name),
            read_only=False,
        )

        self.need_write_access = need_write_access
        self._configure_connection(config_dict)

    def _configure_connection(self, config_dict: ConfigDict) -> None:
        '''Configure S3 credentials for the DuckDB connection. Only read access is required.'''
        s3_access_key_id_var_name = config_dict.get('s3_access_key_id_var_name')
        s3_secret_access_key_var_name = config_dict.get('s3_secret_access_key_var_name')

        self.connection.execute(
            f'''
            install {DUCKDB_EXTENSION_HTTPFS};
            load {DUCKDB_EXTENSION_HTTPFS};
            CREATE OR REPLACE SECRET read_secret (
                TYPE {S3_SECRET_TYPE},
                KEY_ID '{os.getenv(s3_access_key_id_var_name)}',
                SECRET '{os.getenv(s3_secret_access_key_var_name)}',
                REGION '{S3_REGION}',
                ENDPOINT '{S3_ENDPOINT}'
            );
            '''
        )

    def query(self, query: str) -> Any:
        '''Execute a SQL query and return results.'''
        return self.connection.query(query)

    def execute(self, query: str, *args: Any, **kwargs: Any) -> None:
        '''Execute a SQL query without returning results.'''
        self.connection.execute(query, *args, **kwargs)

    def close(self) -> None:
        '''Close the DuckDB connection.'''
        self.connection.close()

    def df(self, query: str) -> Any:
        '''Execute a SQL query and return results as a pandas DataFrame.'''
        return self.connection.query(query).df()


@contextmanager
def duckdb_connection(
    config_dict: ConfigDict, need_write_access: bool = False
) -> Iterator[DuckDBConnection]:
    '''
    Context manager for DuckDB connections.

    Ensures connections are properly closed even if an exception occurs.
    Only read access to S3 is required.

    Args:
        config_dict: Configuration dictionary containing draft_id and S3 credentials.
        need_write_access: Whether write access is needed (deprecated, not used)

    Yields:
        DuckDBConnection: A configured DuckDB connection

    Example:
        >>> with duckdb_connection(config_dict) as conn:
        ...     df = conn.df('SELECT * FROM my_table')
    '''
    conn = DuckDBConnection(config_dict, need_write_access)
    try:
        yield conn
    finally:
        conn.close()
