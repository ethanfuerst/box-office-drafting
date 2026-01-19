import logging
import os

from sqlmesh.core.context import Context

from src import project_root
from src.sheets.runner import run_dashboard
from src.utils.config import ConfigDict


def run_sqlmesh_plan(config_dict: ConfigDict) -> None:
    '''Run SQLMesh plan and apply changes to the database.'''
    logging.info('Syncing google sheet data.')
    os.environ['CONFIG_PATH'] = str(config_dict['path'])

    sqlmesh_context = Context(
        paths=project_root / 'src' / 'dashboard' / 'sqlmesh_project'
    )

    plan = sqlmesh_context.plan()
    sqlmesh_context.apply(plan)
    _ = sqlmesh_context.run()


def google_sheet_sync(config_dict: ConfigDict) -> None:
    '''Run SQLMesh plan and update Google Sheet dashboard with latest data.'''
    run_sqlmesh_plan(config_dict)
    run_dashboard(config_dict)
