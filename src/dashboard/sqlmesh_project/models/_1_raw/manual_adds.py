import typing as t
from datetime import datetime

import pandas as pd
from pandas import DataFrame
from sqlmesh import ExecutionContext, model

from utils.gspread_utils import get_worksheet


@model(
    'raw.manual_adds',
    columns={
        'title': 'text',
        'revenue': 'int',
        'domestic_rev': 'int',
        'foreign_rev': 'int',
        'release_date': 'date',
    },
    column_descriptions={
        'title': 'Title of the movie',
        'revenue': 'Revenue of the movie',
        'domestic_rev': 'Domestic revenue of the movie',
        'foreign_rev': 'Foreign revenue of the movie',
        'release_date': 'Date the movie was released',
    },
)
def execute(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    **kwargs: t.Any,
) -> pd.DataFrame:
    sheet_name = context.var('sheet_name')
    credentials_name = context.var('gspread_credentials_name')

    if not sheet_name:
        raise ValueError('sheet_name must be set in SQLMesh variables')

    worksheet = get_worksheet(sheet_name, 'Manual Adds', credentials_name)

    raw = worksheet.get_all_values()
    df = DataFrame(data=raw[1:], columns=raw[0]).astype(str)
    df['release_date'] = pd.to_datetime(df['release_date'], format='%m/%d/%Y')

    return df
