from unittest.mock import patch

import duckdb
import pandas as pd
import pytest

from tests.conftest import make_config_dict


def test_duckdb_connection_query_returns_result(tmp_path, monkeypatch):
    """Query method executes SQL and returns result."""
    monkeypatch.setenv('TEST_S3_KEY_ID', 'fake_key')
    monkeypatch.setenv('TEST_S3_SECRET', 'fake_secret')

    db_dir = tmp_path / 'src' / 'duckdb_databases'
    db_dir.mkdir(parents=True)

    config = make_config_dict(update_type='s3')
    config['draft_id'] = 'test_query_db'
    config['path'] = tmp_path / 'config.yml'

    with patch('src.utils.db_connection.project_root', tmp_path):
        from src.utils.db_connection import DuckDBConnection

        conn = DuckDBConnection(config)

        conn.execute('CREATE TABLE test_table (id INTEGER, name VARCHAR)')
        conn.execute("INSERT INTO test_table VALUES (1, 'Alice'), (2, 'Bob')")
        result = conn.query('SELECT * FROM test_table ORDER BY id')
        rows = result.fetchall()
        conn.close()

    assert len(rows) == 2
    assert rows[0] == (1, 'Alice')
    assert rows[1] == (2, 'Bob')


def test_duckdb_connection_execute_runs_without_return(tmp_path, monkeypatch):
    """Execute method runs SQL without returning results."""
    monkeypatch.setenv('TEST_S3_KEY_ID', 'fake_key')
    monkeypatch.setenv('TEST_S3_SECRET', 'fake_secret')

    db_dir = tmp_path / 'src' / 'duckdb_databases'
    db_dir.mkdir(parents=True)

    config = make_config_dict(update_type='s3')
    config['draft_id'] = 'test_execute_db'
    config['path'] = tmp_path / 'config.yml'

    with patch('src.utils.db_connection.project_root', tmp_path):
        from src.utils.db_connection import DuckDBConnection

        conn = DuckDBConnection(config)

        conn.execute('CREATE TABLE exec_test (val INTEGER)')
        conn.execute('INSERT INTO exec_test VALUES (42)')
        result = conn.query('SELECT val FROM exec_test')
        rows = result.fetchall()
        conn.close()

    assert rows == [(42,)]


def test_duckdb_connection_df_returns_dataframe(tmp_path, monkeypatch):
    """The df method returns a pandas DataFrame."""
    monkeypatch.setenv('TEST_S3_KEY_ID', 'fake_key')
    monkeypatch.setenv('TEST_S3_SECRET', 'fake_secret')

    db_dir = tmp_path / 'src' / 'duckdb_databases'
    db_dir.mkdir(parents=True)

    config = make_config_dict(update_type='s3')
    config['draft_id'] = 'test_df_db'
    config['path'] = tmp_path / 'config.yml'

    with patch('src.utils.db_connection.project_root', tmp_path):
        from src.utils.db_connection import DuckDBConnection

        conn = DuckDBConnection(config)

        conn.execute('CREATE TABLE df_test (id INTEGER, value DOUBLE)')
        conn.execute('INSERT INTO df_test VALUES (1, 3.14), (2, 2.71)')
        df = conn.df('SELECT * FROM df_test ORDER BY id')
        conn.close()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns) == ['id', 'value']


def test_duckdb_connection_close_closes_connection(tmp_path, monkeypatch):
    """Close method closes the underlying connection."""
    monkeypatch.setenv('TEST_S3_KEY_ID', 'fake_key')
    monkeypatch.setenv('TEST_S3_SECRET', 'fake_secret')

    db_dir = tmp_path / 'src' / 'duckdb_databases'
    db_dir.mkdir(parents=True)

    config = make_config_dict(update_type='s3')
    config['draft_id'] = 'test_close_db'
    config['path'] = tmp_path / 'config.yml'

    with patch('src.utils.db_connection.project_root', tmp_path):
        from src.utils.db_connection import DuckDBConnection

        conn = DuckDBConnection(config)
        conn.close()

        with pytest.raises(duckdb.ConnectionException):
            conn.query('SELECT 1')


def test_duckdb_connection_creates_database_file(tmp_path, monkeypatch):
    """Database file is created at expected location."""
    monkeypatch.setenv('TEST_S3_KEY_ID', 'fake_key')
    monkeypatch.setenv('TEST_S3_SECRET', 'fake_secret')

    db_dir = tmp_path / 'src' / 'duckdb_databases'
    db_dir.mkdir(parents=True)

    config = make_config_dict(update_type='s3')
    config['draft_id'] = 'file_creation_test'
    config['path'] = tmp_path / 'config.yml'

    expected_db_path = db_dir / 'file_creation_test.duckdb'

    with patch('src.utils.db_connection.project_root', tmp_path):
        from src.utils.db_connection import DuckDBConnection

        conn = DuckDBConnection(config)
        conn.close()

    assert expected_db_path.exists()


def test_duckdb_connection_context_manager_yields_connection(tmp_path, monkeypatch):
    """Context manager yields a DuckDBConnection."""
    monkeypatch.setenv('TEST_S3_KEY_ID', 'fake_key')
    monkeypatch.setenv('TEST_S3_SECRET', 'fake_secret')

    db_dir = tmp_path / 'src' / 'duckdb_databases'
    db_dir.mkdir(parents=True)

    config = make_config_dict(update_type='s3')
    config['draft_id'] = 'ctx_mgr_test'
    config['path'] = tmp_path / 'config.yml'

    with patch('src.utils.db_connection.project_root', tmp_path):
        from src.utils.db_connection import duckdb_connection

        with duckdb_connection(config) as conn:
            conn.execute('CREATE TABLE ctx_test (x INTEGER)')
            conn.execute('INSERT INTO ctx_test VALUES (99)')
            result = conn.query('SELECT x FROM ctx_test').fetchall()

    assert result == [(99,)]


def test_duckdb_connection_context_manager_closes_on_exit(tmp_path, monkeypatch):
    """Connection is closed when exiting context."""
    monkeypatch.setenv('TEST_S3_KEY_ID', 'fake_key')
    monkeypatch.setenv('TEST_S3_SECRET', 'fake_secret')

    db_dir = tmp_path / 'src' / 'duckdb_databases'
    db_dir.mkdir(parents=True)

    config = make_config_dict(update_type='s3')
    config['draft_id'] = 'ctx_close_test'
    config['path'] = tmp_path / 'config.yml'

    with patch('src.utils.db_connection.project_root', tmp_path):
        from src.utils.db_connection import duckdb_connection

        with duckdb_connection(config) as conn:
            captured_conn = conn

        with pytest.raises(duckdb.ConnectionException):
            captured_conn.query('SELECT 1')


def test_duckdb_connection_context_manager_closes_on_exception(tmp_path, monkeypatch):
    """Connection is closed even when exception occurs."""
    monkeypatch.setenv('TEST_S3_KEY_ID', 'fake_key')
    monkeypatch.setenv('TEST_S3_SECRET', 'fake_secret')

    db_dir = tmp_path / 'src' / 'duckdb_databases'
    db_dir.mkdir(parents=True)

    config = make_config_dict(update_type='s3')
    config['draft_id'] = 'ctx_exception_test'
    config['path'] = tmp_path / 'config.yml'

    captured_conn = None

    with patch('src.utils.db_connection.project_root', tmp_path):
        from src.utils.db_connection import duckdb_connection

        with pytest.raises(RuntimeError):
            with duckdb_connection(config) as conn:
                captured_conn = conn
                raise RuntimeError('Test error')

        with pytest.raises(duckdb.ConnectionException):
            captured_conn.query('SELECT 1')
