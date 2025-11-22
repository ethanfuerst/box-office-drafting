from typing import Dict, List, Optional

from pandas import DataFrame

from src.utils.db_connection import duckdb_connection


def table_to_df(
    config: Dict,
    table: str,
    columns: Optional[List[str]] = None,
) -> DataFrame:
    catalog_name = config.get('database_file', '').replace('.duckdb', '')

    with duckdb_connection(config) as duckdb_con:
        df = duckdb_con.df(f'select * from {catalog_name}.{table}')

    if columns:
        df.columns = columns

    df = df.replace([float('inf'), float('-inf'), float('nan')], None)

    return df
