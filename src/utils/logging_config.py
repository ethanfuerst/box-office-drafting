import logging

from src.utils.constants import DATETIME_FORMAT


def setup_logging() -> None:
    '''Configure basic logging with INFO level and file output.'''
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt=DATETIME_FORMAT,
        filemode='a',
    )
