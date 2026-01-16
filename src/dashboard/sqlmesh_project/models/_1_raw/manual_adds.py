import json
import os
import typing as t
from datetime import datetime

import pandas as pd
from eftoolkit.gsheets import Spreadsheet
from sqlmesh import ExecutionContext, model


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
) -> t.Iterator[pd.DataFrame]:
    sheet_name = context.var('sheet_name')
    credentials_name = context.var('gspread_credentials_name')

    if not sheet_name:
        raise ValueError('sheet_name must be set in SQLMesh variables')

    credentials_json = os.getenv(credentials_name)
    credentials_dict = json.loads(credentials_json.replace('\n', '\\n'))

    with Spreadsheet(credentials=credentials_dict, spreadsheet_name=sheet_name) as ss:
        df = ss.worksheet('Manual Adds').read()

    if df.empty:
        yield from ()
        return

    df = df.astype(str)
    df['release_date'] = pd.to_datetime(df['release_date'], format='%m/%d/%Y')

    yield df
