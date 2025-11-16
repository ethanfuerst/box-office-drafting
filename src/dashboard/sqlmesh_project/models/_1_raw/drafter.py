import typing as t
from datetime import datetime

import pandas as pd
from pandas import DataFrame
from sqlmesh import ExecutionContext, model

from utils.gspread_utils import get_worksheet


@model(
    'raw.drafter',
    columns={
        'round': 'int',
        'overall_pick': 'int',
        'name': 'text',
        'movie': 'text',
    },
    column_descriptions={
        'round': 'Round number of draft',
        'overall_pick': 'Overall pick number of draft',
        'name': 'Name of the person picking',
        'movie': 'Movie picked',
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

    worksheet = get_worksheet(sheet_name, 'Draft', credentials_name)

    raw = worksheet.get_all_values()
    df = DataFrame(data=raw[1:], columns=raw[0]).astype(str)

    return df
