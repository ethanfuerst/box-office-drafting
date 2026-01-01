import json
import os

from gspread import service_account_from_dict


def get_gspread_client(credentials_name: str = None):
    '''Helper function to get Google Sheets client with credentials.'''
    if credentials_name is None:
        credentials_name = os.getenv('GSPREAD_CREDENTIALS_NAME')

    if not credentials_name:
        raise ValueError(
            'GSPREAD_CREDENTIALS_NAME must be set as environment variable or passed as parameter'
        )

    credentials_json = os.getenv(credentials_name)
    if credentials_json is None:
        raise ValueError(
            f'Environment variable "{credentials_name}" is not set. '
            'Ensure the credentials are available as an environment variable.'
        )

    credentials_dict = json.loads(os.getenv(credentials_name).replace('\n', '\\n'))
    return service_account_from_dict(credentials_dict)


def get_worksheet(sheet_name: str, worksheet_name: str, credentials_name: str = None):
    '''Helper function to get a specific worksheet from a Google Sheet.'''
    gc = get_gspread_client(credentials_name)
    return gc.open(sheet_name).worksheet(worksheet_name)
