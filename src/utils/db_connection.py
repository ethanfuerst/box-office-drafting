import os
from contextlib import contextmanager
from typing import Any, Iterator, cast

import duckdb
from dotenv import load_dotenv

from src import project_root
from src.utils.config_types import ConfigDict
from src.utils.constants import (
    DUCKDB_EXTENSION_HTTPFS,
    S3_ENDPOINT,
    S3_REGION,
    S3_SECRET_TYPE,
)

load_dotenv()


class DuckDBConnection:
    def __init__(self, config: ConfigDict, need_write_access: bool = False) -> None:
        '''Initialize a DuckDB connection with S3 configuration.'''
        database_name = (
            project_root / 'src' / 'duckdb_databases' / config.get('database_file')
        )

        self.connection = duckdb.connect(
            database=str(database_name),
            read_only=False,
        )

        self.need_write_access = need_write_access
        self._configure_connection(config)

    def _configure_connection(self, config: ConfigDict) -> None:
        '''Configure S3 credentials for the DuckDB connection.'''
        access_type = 'write' if self.need_write_access else 'read'
        s3_access_key_id_var_name = cast(
            str,
            config.get(f's3_{access_type}_access_key_id_var_name', 'S3_ACCESS_KEY_ID'),
        )
        s3_secret_access_key_var_name = cast(
            str,
            config.get(
                f's3_{access_type}_secret_access_key_var_name', 'S3_SECRET_ACCESS_KEY'
            ),
        )

        self.connection.execute(
            f'''
            install {DUCKDB_EXTENSION_HTTPFS};
            load {DUCKDB_EXTENSION_HTTPFS};
            CREATE OR REPLACE SECRET {access_type}_secret (
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
    config: ConfigDict, need_write_access: bool = False
) -> Iterator[DuckDBConnection]:
    '''
    Context manager for DuckDB connections.

    Ensures connections are properly closed even if an exception occurs.

    Args:
        config: Configuration dictionary containing database_file and S3 credentials.
        need_write_access: Whether write access is needed (affects S3 secret naming)

    Yields:
        DuckDBConnection: A configured DuckDB connection

    Example:
        >>> with duckdb_connection(config) as conn:
        ...     df = conn.df('SELECT * FROM my_table')
    '''
    conn = DuckDBConnection(config, need_write_access)
    try:
        yield conn
    finally:
        conn.close()
