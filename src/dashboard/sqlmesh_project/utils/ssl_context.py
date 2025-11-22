import ssl
from contextlib import contextmanager
from typing import Iterator


@contextmanager
def unverified_ssl_context() -> Iterator[None]:
    '''
    Temporarily disable SSL verification (use with caution).

    This context manager temporarily disables SSL certificate verification
    for HTTPS connections. Only use when necessary (e.g., scraping websites
    with self-signed certificates).

    Warning: This makes connections vulnerable to man-in-the-middle attacks.
    '''
    old_context = ssl._create_default_https_context
    ssl._create_default_https_context = ssl._create_unverified_context
    try:
        yield
    finally:
        ssl._create_default_https_context = old_context
