import logging
import os
import ssl

from sqlmesh.core.context import Context

from src import project_root
from src.utils.gsheet import GoogleSheetDashboard, load_dashboard_data
from src.utils.read_config import get_config_dict

ssl._create_default_https_context = ssl._create_unverified_context


def run_sqlmesh_plan(config_path: str) -> None:
    logging.info('Syncing google sheet data.')
    os.environ['CONFIG_PATH'] = str(config_path)

    sqlmesh_context = Context(
        paths=project_root / 'src' / 'dashboard' / 'sqlmesh_project'
    )

    plan = sqlmesh_context.plan()
    sqlmesh_context.apply(plan)
    _ = sqlmesh_context.run()


def google_sheet_sync(config_path: str) -> None:
    run_sqlmesh_plan(config_path)
    load_dashboard_data(config_path)
