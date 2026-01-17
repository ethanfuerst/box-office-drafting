import json
import os
import typing as t
from datetime import datetime

import pandas as pd
from eftoolkit.gsheets import Spreadsheet
from sqlmesh import ExecutionContext, model


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

    credentials_json = os.getenv(credentials_name)
    credentials_dict = json.loads(credentials_json.replace('\n', '\\n'))

    with Spreadsheet(credentials=credentials_dict, spreadsheet_name=sheet_name) as ss:
        df = ss.worksheet('Multipliers and Exclusions').read()

    if df.empty:
        yield from ()
        return

    df = df.astype(str)
    df['multiplier'] = df['multiplier'].replace('', 0).astype(float)

    yield df
