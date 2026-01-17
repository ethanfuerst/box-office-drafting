import json
import os
import typing as t
from datetime import datetime

import pandas as pd
from eftoolkit.gsheets import Spreadsheet
from sqlmesh import ExecutionContext, model


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

    credentials_json = os.getenv(credentials_name)
    credentials_dict = json.loads(credentials_json.replace('\n', '\\n'))

    with Spreadsheet(credentials=credentials_dict, spreadsheet_name=sheet_name) as ss:
        df = ss.worksheet('Draft').read()

    return df.astype(str)
