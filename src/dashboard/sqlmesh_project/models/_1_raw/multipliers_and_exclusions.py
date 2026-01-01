import typing as t
from datetime import datetime

import pandas as pd
from pandas import DataFrame
from sqlmesh import ExecutionContext, model

from utils.gspread_utils import get_worksheet


@model(
    'raw.multipliers_and_exclusions',
    columns={
        'value': 'text',
        'multiplier': 'double',
        'type': 'text',
    },
    column_descriptions={
        'value': 'Value of the record',
        'multiplier': 'Multiplier of the record',
        'type': 'Type of the record',
    },
)
def execute(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    **kwargs: t.Any,
) -> t.Iterator[pd.DataFrame]:
    sheet_name = context.var('sheet_name')
    credentials_name = context.var('gspread_credentials_name')

    if not sheet_name:
        raise ValueError('sheet_name must be set in SQLMesh variables')

    worksheet = get_worksheet(
        sheet_name, 'Multipliers and Exclusions', credentials_name
    )

    raw = worksheet.get_all_values()

    # Handle empty worksheet
    if len(raw) <= 1:
        yield from ()
        return

    df = DataFrame(data=raw[1:], columns=raw[0]).astype(str)
    df['multiplier'] = df['multiplier'].replace('', 0).astype(float)

    yield df
