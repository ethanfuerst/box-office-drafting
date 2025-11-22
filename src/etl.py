import logging
import os
from pathlib import Path

from sqlmesh.core.context import Context

from src import project_root
from src.utils.gsheet import load_dashboard_data


def run_sqlmesh_plan(config_path: Path | str) -> None:
    '''Run SQLMesh plan and apply changes to the database.'''
    logging.info('Syncing google sheet data.')
    config_path_obj = Path(config_path)
    os.environ['CONFIG_PATH'] = str(config_path_obj)

    sqlmesh_context = Context(
        paths=project_root / 'src' / 'dashboard' / 'sqlmesh_project'
    )

    plan = sqlmesh_context.plan(restate_models=['raw.*'])
    sqlmesh_context.apply(plan)
    _ = sqlmesh_context.run()


def google_sheet_sync(config_path: Path | str) -> None:
    '''Run SQLMesh plan and update Google Sheet dashboard with latest data.'''
    run_sqlmesh_plan(config_path)
    load_dashboard_data(config_path)
