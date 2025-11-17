import datetime
import logging
import os
import ssl
from typing import Dict

from pandas import read_html
from sqlmesh.core.context import Context

from src import project_root
from src.utils.db_connection import DuckDBConnection
from src.utils.gsheet import (
    GoogleSheetDashboard,
    apply_conditional_formatting,
    log_min_revenue_info,
    log_missing_movies,
    update_dashboard,
    update_titles,
)
from src.utils.read_config import get_config_dict
from src.utils.s3_utils import load_df_to_s3_table

S3_DATE_FORMAT = '%Y-%m-%d'


ssl._create_default_https_context = ssl._create_unverified_context


def load_worldwide_box_office_to_s3(
    duckdb_con: DuckDBConnection,
    year: int,
    bucket: str,
) -> int:
    logging.info(f'Starting extraction for {year}.')

    try:
        df = read_html(f'https://www.boxofficemojo.com/year/world/{year}')[0]
    except Exception as e:
        logging.error(f'Failed to fetch data: {e}')
        return 0

    formatted_date = datetime.date.today().strftime(S3_DATE_FORMAT)

    s3_key = f'release_year={year}/scraped_date={formatted_date}/data'

    rows_loaded = load_df_to_s3_table(
        duckdb_con=duckdb_con,
        df=df,
        s3_key=s3_key,
        bucket_name=bucket,
    )

    return rows_loaded


def s3_sync(config_path: str) -> None:
    logging.info('Extracting worldwide box office data.')
    config = get_config_dict(config_path)

    duckdb_con = DuckDBConnection(
        config=config,
        need_write_access=True,
    ).connection

    current_year = datetime.date.today().year
    last_year = current_year - 1

    logging.info(f'Running for {current_year} and {last_year}')

    total_rows_loaded = 0
    bucket = config['bucket']

    for year in [current_year, last_year]:
        total_rows_loaded += load_worldwide_box_office_to_s3(
            duckdb_con=duckdb_con, year=year, bucket=bucket
        )

    logging.info(f'Total rows loaded to {bucket}: {total_rows_loaded}')


def run_sqlmesh_plan(config_path: str) -> None:
    logging.info('Syncing google sheet data.')
    os.environ['CONFIG_PATH'] = str(config_path)

    sqlmesh_context = Context(
        paths=project_root / 'src' / 'dashboard' / 'sqlmesh_project'
    )

    plan = sqlmesh_context.plan()
    sqlmesh_context.apply(plan)
    _ = sqlmesh_context.run()


def load_dashboard_data(config_path: str) -> None:
    config = get_config_dict(config_path)
    gsheet_dashboard = GoogleSheetDashboard(config)

    update_dashboard(gsheet_dashboard)
    update_titles(gsheet_dashboard)
    apply_conditional_formatting(gsheet_dashboard)
    log_missing_movies(gsheet_dashboard)
    log_min_revenue_info(gsheet_dashboard, config)


def google_sheet_sync(config_path: str) -> None:
    run_sqlmesh_plan(config_path)
    load_dashboard_data(config_path)
