from typing import List, Optional

from pandas import DataFrame

from src.utils.config import ConfigDict
from src.utils.db_connection import get_duckdb


def table_to_df(
    config_dict: ConfigDict,
    table: str,
    columns: Optional[List[str]] = None,
) -> DataFrame:
    '''Load a SQL table into a pandas DataFrame.'''
    catalog_name = config_dict.get('draft_id')

    with get_duckdb(config_dict) as db:
        df = db.query(f'select * from {catalog_name}.{table}')

    if columns:
        df.columns = columns

    df = df.replace([float('inf'), float('-inf'), float('nan')], None)

    return df
