import logging
import os

from sqlmesh.core.context import Context

from src import project_root
from src.utils.config import ConfigDict
from src.utils.gsheet import (
    GoogleSheetDashboard,
    add_comments_to_dashboard,
    apply_conditional_formatting,
    log_min_revenue_info,
    log_missing_movies,
    update_dashboard,
    update_titles,
)


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


def load_dashboard_data(config_dict: ConfigDict) -> None:
    '''Load configuration and update the Google Sheet dashboard.'''
    gsheet_dashboard = GoogleSheetDashboard(config_dict)
    update_dashboard(gsheet_dashboard, config_dict)
    update_titles(gsheet_dashboard)
    apply_conditional_formatting(gsheet_dashboard)
    add_comments_to_dashboard(gsheet_dashboard)
    log_missing_movies(gsheet_dashboard)
    log_min_revenue_info(gsheet_dashboard, config_dict)


def google_sheet_sync(config_dict: ConfigDict) -> None:
    '''Run SQLMesh plan and update Google Sheet dashboard with latest data.'''
    run_sqlmesh_plan(config_dict)
    load_dashboard_data(config_dict)
