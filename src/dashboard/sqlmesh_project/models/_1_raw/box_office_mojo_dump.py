import typing as t
from datetime import datetime, timezone

import pandas as pd
from pandas import read_html
from sqlmesh import ExecutionContext, model

from utils.ssl_context import unverified_ssl_context


@model(
    'raw.box_office_mojo_dump',
    kind='FULL',
    columns={
        'title': 'text',
        'revenue': 'int',
        'domestic_rev': 'int',
        'foreign_rev': 'int',
        'loaded_date': 'date',
        'release_year': 'text',
        'published_timestamp_utc': 'timestamp',
    },
)
def execute(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    **kwargs: t.Any,
) -> pd.DataFrame:
    update_type = context.var('update_type') or 's3'
    year = int(context.var('year') or 2025)
    bucket = context.var('bucket') or ''

    if update_type == 's3':
        s3_query = f"""
        select
            title,
            revenue,
            domestic_rev,
            foreign_rev,
            loaded_date,
            release_year,
            published_timestamp_utc
        from read_parquet('s3://{bucket}/published_tables/daily_ranks/v1/data.parquet')"""

        result_df = context.engine_adapter.fetchdf(s3_query)
    else:
        with unverified_ssl_context():
            df = read_html(f'https://www.boxofficemojo.com/year/world/{year}')[0]

        result_df = df.copy()
        result_df['title'] = result_df['Release Group']
        result_df['revenue'] = (
            result_df['Worldwide']
            .str[2:]
            .str.replace(',', '')
            .astype(int, errors='coerce')
            .fillna(0)
        )
        result_df['domestic_rev'] = (
            result_df['Domestic']
            .str[2:]
            .str.replace(',', '')
            .astype(int, errors='coerce')
            .fillna(0)
        )
        result_df['foreign_rev'] = (
            result_df['Foreign']
            .str[2:]
            .str.replace(',', '')
            .astype(int, errors='coerce')
            .fillna(0)
        )
        result_df['loaded_date'] = pd.Timestamp.now().date()
        result_df['release_year'] = str(year)
        result_df['published_timestamp_utc'] = pd.Timestamp.now(timezone.utc)

        result_df = result_df[
            [
                'title',
                'revenue',
                'domestic_rev',
                'foreign_rev',
                'loaded_date',
                'release_year',
                'published_timestamp_utc',
            ]
        ].copy()

    return result_df
