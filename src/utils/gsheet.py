import json
import logging
import os
from datetime import datetime, timezone

from eftoolkit import load_json_config
from eftoolkit.gsheets import Spreadsheet

from src import project_root
from src.utils.config import ConfigDict
from src.utils.db_connection import get_duckdb
from src.utils.query import table_to_df

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'


def calculate_picks_table_layout(
    scoreboard_length: int,
    released_movies_length: int,
    worst_picks_length: int,
    best_picks_length: int,
) -> dict:
    """
    Calculate the layout for picks tables based on available space.

    Args:
        scoreboard_length: Number of rows in scoreboard (not including header)
        released_movies_length: Number of rows in released movies (not including header)
        worst_picks_length: Number of rows in worst picks data (not including header)
        best_picks_length: Number of rows in best picks data (not including header)

    Returns:
        dict with layout information including row numbers and heights
    """
    available_height = released_movies_length - scoreboard_length - 3
    picks_row_num = 5 + scoreboard_length + 2
    add_both_picks_tables = False
    best_picks_row_num = None
    worst_picks_height = 0
    best_picks_height = 0

    min_rows_per_table = 2
    separator_rows = 2
    total_required = min_rows_per_table * 2 + separator_rows

    if (
        available_height >= total_required
        and worst_picks_length > 1
        and best_picks_length > 1
    ):
        add_both_picks_tables = True
        usable_height = available_height - 2 - separator_rows
        height_per_table = usable_height // 2
        worst_picks_height = min(height_per_table, worst_picks_length)
        best_picks_row_num = picks_row_num + 1 + worst_picks_height + separator_rows
        best_picks_height = min(usable_height - worst_picks_height, best_picks_length)
    else:
        if available_height > 0 and worst_picks_length > 1:
            worst_picks_height = min(available_height, worst_picks_length)

    return {
        'available_height': available_height,
        'add_both_picks_tables': add_both_picks_tables,
        'worst_picks_row_num': picks_row_num,
        'worst_picks_height': worst_picks_height,
        'best_picks_row_num': best_picks_row_num,
        'best_picks_height': best_picks_height,
    }


class GoogleSheetDashboard:
    def __init__(self, config_dict: ConfigDict) -> None:
        """Initialize a Google Sheet dashboard with data from DuckDB."""
        self.config = config_dict
        self.year = self.config['year']
        self.gspread_credentials_name = self.config['gspread_credentials_name']
        self.dashboard_name = self.config['name']
        self.sheet_name = self.config['sheet_name']
        self.released_movies_df = table_to_df(
            self.config,
            'combined.base_query',
            columns=[
                'Rank',
                'Title',
                'Drafted By',
                'Revenue',
                'Scored Revenue',
                'Round Drafted',
                'Overall Pick',
                'Multiplier',
                'Domestic Revenue',
                'Domestic Revenue %',
                'Foreign Revenue',
                'Foreign Revenue %',
                'Better Pick',
                'Better Pick Scored Revenue',
                'First Seen Date',
                'Still In Theaters',
            ],
        )

        self.scoreboard_df = table_to_df(
            config_dict,
            'dashboards.scoreboard',
            columns=[
                'Name',
                'Scored Revenue',
                '# Released',
                '# Optimal Picks',
                '% Optimal Picks',
                'Unadjusted Revenue',
            ],
        )

        self.worst_picks_df = table_to_df(
            config_dict,
            'dashboards.worst_picks',
            columns=[
                'Rank',
                'Title',
                'Drafted By',
                'Overall Pick',
                'Number of Better Picks',
                'Missed Revenue',
            ],
        )

        self.best_picks_df = table_to_df(
            config_dict,
            'dashboards.best_picks',
            columns=[
                'Rank',
                'Title',
                'Drafted By',
                'Overall Pick',
                'Positions Gained',
                'Actual Revenue',
            ],
        )

        self.dashboard_elements = [
            (
                self.scoreboard_df,
                'B4',
                load_json_config(
                    project_root / 'src' / 'assets' / 'scoreboard_format.json',
                    strip_comment_keys=True,
                ),
            ),
            (
                self.released_movies_df,
                'I4',
                load_json_config(
                    project_root / 'src' / 'assets' / 'released_movies_format.json',
                    strip_comment_keys=True,
                ),
            ),
        ]

        layout = calculate_picks_table_layout(
            scoreboard_length=len(self.scoreboard_df),
            released_movies_length=len(self.released_movies_df),
            worst_picks_length=len(self.worst_picks_df),
            best_picks_length=len(self.best_picks_df),
        )

        self.picks_row_num = layout['worst_picks_row_num']
        self.add_both_picks_tables = layout['add_both_picks_tables']
        self.best_picks_row_num = layout['best_picks_row_num']
        self.add_picks_table = (
            layout['worst_picks_height'] > 0
            and len(self.worst_picks_df) > 1
        )

        if layout['add_both_picks_tables']:
            self.worst_picks_df = self.worst_picks_df.head(layout['worst_picks_height'])
            self.best_picks_df = self.best_picks_df.head(layout['best_picks_height'])

            self.dashboard_elements.append(
                (
                    self.worst_picks_df,
                    f'B{self.picks_row_num}',
                    {
                        key.replace('12', str(self.picks_row_num)).replace(
                            '13', str(self.picks_row_num + 1)
                        ): value
                        for key, value in load_json_config(
                            project_root / 'src' / 'assets' / 'worst_picks_format.json',
                            strip_comment_keys=True,
                        ).items()
                    },
                )
            )

            self.dashboard_elements.append(
                (
                    self.best_picks_df,
                    f'B{self.best_picks_row_num}',
                    {
                        key.replace('12', str(self.best_picks_row_num)).replace(
                            '13', str(self.best_picks_row_num + 1)
                        ): value
                        for key, value in load_json_config(
                            project_root / 'src' / 'assets' / 'worst_picks_format.json',
                            strip_comment_keys=True,
                        ).items()
                    },
                )
            )

            logging.info(
                f"Showing both picks tables: worst_picks ({layout['worst_picks_height']} rows) "
                f"and best_picks ({layout['best_picks_height']} rows)"
            )
        elif self.add_picks_table:
            self.worst_picks_df = self.worst_picks_df.head(layout['worst_picks_height'])

            self.dashboard_elements.append(
                (
                    self.worst_picks_df,
                    f'B{self.picks_row_num}',
                    {
                        key.replace('12', str(self.picks_row_num)).replace(
                            '13', str(self.picks_row_num + 1)
                        ): value
                        for key, value in load_json_config(
                            project_root / 'src' / 'assets' / 'worst_picks_format.json',
                            strip_comment_keys=True,
                        ).items()
                    },
                )
            )

        self.setup_worksheet()

    def setup_worksheet(self) -> None:
        """Create and configure the Google Sheet worksheet."""
        gspread_credentials_key = self.gspread_credentials_name
        gspread_credentials = os.getenv(gspread_credentials_key)

        if gspread_credentials is not None:
            credentials_dict = json.loads(gspread_credentials.replace('\n', '\\n'))
        else:
            raise ValueError(
                f'{gspread_credentials_key} is not set or is invalid in the .env file.'
            )

        self.sheet_height = len(self.released_movies_df) + 5

        with Spreadsheet(
            credentials=credentials_dict, spreadsheet_name=self.sheet_name
        ) as ss:
            existing_worksheets = ss.get_worksheet_names()
            if 'Manual Adds' not in existing_worksheets:
                ss.create_worksheet('Manual Adds', rows=100, cols=10)
            if 'Multipliers and Exclusions' not in existing_worksheets:
                ss.create_worksheet('Multipliers and Exclusions', rows=100, cols=10)
            if 'Dashboard' in existing_worksheets:
                ss.delete_worksheet('Dashboard')
            ss.create_worksheet('Dashboard', rows=self.sheet_height, cols=25)

            ss.reorder_worksheets(
                ['Dashboard', 'Draft', 'Manual Adds', 'Multipliers and Exclusions']
            )

        self._credentials_dict = credentials_dict


def update_dashboard(
    gsheet_dashboard: GoogleSheetDashboard, config_dict: ConfigDict
) -> None:
    """Update the Google Sheet with dashboard data and metadata."""
    with Spreadsheet(
        credentials=gsheet_dashboard._credentials_dict,
        spreadsheet_name=gsheet_dashboard.sheet_name,
    ) as ss:
        ws = ss.worksheet('Dashboard')

        for element in gsheet_dashboard.dashboard_elements:
            ws.write_dataframe(
                df=element[0],
                location=element[1],
                format_dict=element[2] if len(element) > 2 else None,
            )

        dashboard_done_updating = (
            gsheet_dashboard.released_movies_df['Still In Theaters'].eq('No').all()
            and len(gsheet_dashboard.released_movies_df) > 0
            and gsheet_dashboard.year < datetime.now(timezone.utc).year
        )

        log_string = f'Dashboard Last Updated\n{datetime.now(timezone.utc).strftime(DATETIME_FORMAT)} UTC'

        if dashboard_done_updating:
            log_string += '\nDashboard is done updating\nand can be removed from the etl'

        with get_duckdb(config_dict) as db:
            published_timestamp_of_most_recent_data = db.connection.query(
                """
                    select max(published_timestamp_utc) as published_timestamp_utc
                    from cleaned.box_office_mojo_dump
                """
            ).fetchnumpy()['published_timestamp_utc'][0]

        dt = published_timestamp_of_most_recent_data.item()
        log_string += f'\nData Updated Through\n{dt.strftime(DATETIME_FORMAT)} UTC'

        ws.write_values('G2', [[log_string]])
        ws.format_range(
            'G2',
            {
                'horizontalAlignment': 'CENTER',
            },
        )

        ws.auto_resize_columns(1, 7)
        ws.auto_resize_columns(8, 23)

        ws.format_range(
            'B4:G4',
            {
                'horizontalAlignment': 'CENTER',
                'textFormat': {
                    'fontSize': 10,
                    'bold': True,
                },
            },
        )

        if gsheet_dashboard.add_picks_table:
            if gsheet_dashboard.add_both_picks_tables:
                ws.format_range(
                    f'B{gsheet_dashboard.picks_row_num}:G{gsheet_dashboard.picks_row_num}',
                    {
                        'horizontalAlignment': 'CENTER',
                        'textFormat': {
                            'fontSize': 10,
                            'bold': True,
                        },
                    },
                )
                ws.format_range(
                    f'B{gsheet_dashboard.best_picks_row_num}:G{gsheet_dashboard.best_picks_row_num}',
                    {
                        'horizontalAlignment': 'CENTER',
                        'textFormat': {
                            'fontSize': 10,
                            'bold': True,
                        },
                    },
                )
            else:
                ws.format_range(
                    f'B{gsheet_dashboard.picks_row_num}:G{gsheet_dashboard.picks_row_num}',
                    {
                        'horizontalAlignment': 'CENTER',
                        'textFormat': {
                            'fontSize': 10,
                            'bold': True,
                        },
                    },
                )

        ws.format_range(
            'I4:X4',
            {
                'horizontalAlignment': 'CENTER',
                'textFormat': {
                    'fontSize': 10,
                    'bold': True,
                },
            },
        )

        all_data = ws.read()
        if not all_data.empty and 'V' in all_data.columns:
            v_col_idx = list(all_data.columns).index('V')
            for i in range(4, len(all_data)):  # Start at row 5 (index 4)
                cell_value = all_data.iloc[i, v_col_idx] if i < len(all_data) else None
                if cell_value == '$0':
                    ws.write_values(f'V{i + 1}', [['']])

        spacer_columns = ['A', 'H', 'Y']
        for column in spacer_columns:
            ws.set_column_width(column, 25)

        title_columns = ['J', 'U']

        if gsheet_dashboard.add_picks_table:
            title_columns.append('C')

        for column in title_columns:
            ws.set_column_width(column, 284)

        revenue_columns = ['L', 'M', 'R', 'S']
        for column in revenue_columns:
            ws.set_column_width(column, 120)

        ws.set_column_width('G', 164)
        ws.set_column_width('R', 142)
        ws.set_column_width('W', 104)
        ws.set_column_width('X', 106)

        if dashboard_done_updating:
            ws.set_column_width('G', 200)


def update_titles(gsheet_dashboard: GoogleSheetDashboard) -> None:
    """Update section titles in the Google Sheet."""
    with Spreadsheet(
        credentials=gsheet_dashboard._credentials_dict,
        spreadsheet_name=gsheet_dashboard.sheet_name,
    ) as ss:
        ws = ss.worksheet('Dashboard')

        ws.write_values('B2', [[gsheet_dashboard.dashboard_name]])
        ws.format_range(
            'B2',
            {'horizontalAlignment': 'CENTER', 'textFormat': {'fontSize': 20, 'bold': True}},
        )
        ws.merge_cells('B2:F2')
        ws.write_values('I2', [['Released Movies']])
        ws.format_range(
            'I2',
            {'horizontalAlignment': 'CENTER', 'textFormat': {'fontSize': 20, 'bold': True}},
        )
        ws.merge_cells('I2:X2')

        if gsheet_dashboard.add_picks_table:
            if gsheet_dashboard.add_both_picks_tables:
                worst_picks_title_row_num = gsheet_dashboard.picks_row_num - 1
                ws.write_values(
                    f'B{worst_picks_title_row_num}',
                    [['Worst Picks']],
                )
                ws.format_range(
                    f'B{worst_picks_title_row_num}',
                    {'horizontalAlignment': 'CENTER', 'textFormat': {'bold': True}},
                )
                ws.merge_cells(
                    f'B{worst_picks_title_row_num}:G{worst_picks_title_row_num}'
                )

                best_picks_title_row_num = gsheet_dashboard.best_picks_row_num - 1
                ws.write_values(
                    f'B{best_picks_title_row_num}',
                    [['Best Picks']],
                )
                ws.format_range(
                    f'B{best_picks_title_row_num}',
                    {'horizontalAlignment': 'CENTER', 'textFormat': {'bold': True}},
                )
                ws.merge_cells(
                    f'B{best_picks_title_row_num}:G{best_picks_title_row_num}'
                )
            else:
                picks_title_row_num = gsheet_dashboard.picks_row_num - 1
                ws.write_values(
                    f'B{picks_title_row_num}',
                    [['Worst Picks']],
                )
                ws.format_range(
                    f'B{picks_title_row_num}',
                    {'horizontalAlignment': 'CENTER', 'textFormat': {'bold': True}},
                )
                ws.merge_cells(
                    f'B{picks_title_row_num}:G{picks_title_row_num}'
                )


def apply_conditional_formatting(gsheet_dashboard: GoogleSheetDashboard) -> None:
    """Apply conditional formatting rules to the Google Sheet."""
    with Spreadsheet(
        credentials=gsheet_dashboard._credentials_dict,
        spreadsheet_name=gsheet_dashboard.sheet_name,
    ) as ss:
        ws = ss.worksheet('Dashboard')
        end_row = gsheet_dashboard.sheet_height
        ws.add_conditional_format(
            f'X5:X{end_row}',
            {
                'type': 'TEXT_EQ',
                'values': ['Yes'],
                'format': {'backgroundColor': {'red': 0, 'green': 0.9, 'blue': 0}},
            },
        )

    logging.info('Dashboard updated and formatted')


def add_comments_to_dashboard(gsheet_dashboard: GoogleSheetDashboard) -> None:
    """Add comments to the dashboard."""
    notes_dict = load_json_config(
        project_root / 'src' / 'assets' / 'dashboard_notes.json',
        strip_comment_keys=True,
    )

    with Spreadsheet(
        credentials=gsheet_dashboard._credentials_dict,
        spreadsheet_name=gsheet_dashboard.sheet_name,
    ) as ss:
        ws = ss.worksheet('Dashboard')
        ws.set_notes(notes_dict)


def log_missing_movies(gsheet_dashboard: GoogleSheetDashboard) -> None:
    """Log movies that are drafted but missing from the scoreboard."""
    draft_df = table_to_df(
        gsheet_dashboard.config,
        'cleaned.drafter',
    )
    released_movies = [
        str(movie) for movie in gsheet_dashboard.released_movies_df['Title'].tolist()
    ]
    drafted_movies = [str(movie) for movie in draft_df['movie'].tolist()]
    movies_missing_from_scoreboard = list(set(drafted_movies) - set(released_movies))

    if movies_missing_from_scoreboard:
        logging.info(
            'The following movies are missing from the scoreboard and should be added to the manual_adds.csv file:'
        )
        logging.info(', '.join(sorted(movies_missing_from_scoreboard)))
    else:
        logging.info('All movies are on the scoreboard.')


def log_min_revenue_info(
    gsheet_dashboard: GoogleSheetDashboard, config_dict: ConfigDict
) -> None:
    """Log movies with revenue below the minimum threshold."""
    with get_duckdb(config_dict) as db:
        result = db.connection.query(
            f"""
            with most_recent_data as (
                select title, revenue
                from cleaned.box_office_mojo_dump where release_year = {gsheet_dashboard.year}
                qualify rank() over (order by loaded_date desc) = 1
                order by 2 desc
            )

            select title, revenue
            from most_recent_data qualify row_number() over (order by revenue asc) = 1;
            """
        ).fetchnumpy()['revenue']

        if len(result) == 0:
            logging.info('No revenue data found for this year.')
            return

        min_revenue_of_most_recent_data = result[0]

        logging.info(
            f'Minimum revenue of most recent data: {min_revenue_of_most_recent_data}'
        )

        movies_under_min_revenue = (
            db.connection.query(
                f"""
                with cleaned_data as (
                    select title, revenue
                    from cleaned.box_office_mojo_dump
                    where release_year = {gsheet_dashboard.year}
                    qualify row_number() over (partition by title order by loaded_date desc) = 1
                )

                select cleaned_data.title from cleaned_data
                inner join combined.base_query as base_query
                    on cleaned_data.title = base_query.title
                where cleaned_data.revenue <= {min_revenue_of_most_recent_data}
                """
            )
            .fetchnumpy()['title']
            .tolist()
        )

    if movies_under_min_revenue:
        logging.info(
            'The most recent records for the following movies are under the minimum revenue of the most recent data pull'
            + ' and may not have the correct revenue and should be added to the manual_adds.csv file:'
        )
        logging.info(', '.join(sorted(movies_under_min_revenue)))
    else:
        logging.info(
            'All movies are above the minimum revenue of the most recent data pull.'
        )
