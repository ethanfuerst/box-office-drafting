import duckdb
import pandas as pd
import pytest
from eftoolkit.sql import DuckDB

from src.utils.db_connection import get_duckdb
from tests.conftest import make_config_dict


class TestGetDuckdb:
    """Tests for get_duckdb factory function."""

    def test_returns_duckdb_instance(self, tmp_path, monkeypatch):
        """Returns an eftoolkit.sql.DuckDB instance."""
        monkeypatch.setattr(
            'src.utils.db_connection.project_root',
            tmp_path,
        )

        db_dir = tmp_path / 'src' / 'duckdb_databases'
        db_dir.mkdir(parents=True)

        config = make_config_dict(update_type='s3')
        config['draft_id'] = 'test_returns_instance'

        db = get_duckdb(config)

        assert isinstance(db, DuckDB)
        db.close()

    def test_creates_database_file(self, tmp_path, monkeypatch):
        """Database file is created at expected location."""
        monkeypatch.setattr(
            'src.utils.db_connection.project_root',
            tmp_path,
        )

        db_dir = tmp_path / 'src' / 'duckdb_databases'
        db_dir.mkdir(parents=True)

        config = make_config_dict(update_type='s3')
        config['draft_id'] = 'file_creation_test'

        expected_db_path = db_dir / 'file_creation_test.duckdb'

        with get_duckdb(config) as db:
            db.execute('SELECT 1')

        assert expected_db_path.exists()

    def test_context_manager_works(self, tmp_path, monkeypatch):
        """Context manager provides persistent connection."""
        monkeypatch.setattr(
            'src.utils.db_connection.project_root',
            tmp_path,
        )

        db_dir = tmp_path / 'src' / 'duckdb_databases'
        db_dir.mkdir(parents=True)

        config = make_config_dict(update_type='s3')
        config['draft_id'] = 'test_context_manager'

        with get_duckdb(config) as db:
            db.execute('CREATE TABLE test_table (id INTEGER, name VARCHAR)')
            db.execute("INSERT INTO test_table VALUES (1, 'Alice'), (2, 'Bob')")
            result = db.connection.query('SELECT * FROM test_table ORDER BY id')
            rows = result.fetchall()

        assert len(rows) == 2
        assert rows[0] == (1, 'Alice')
        assert rows[1] == (2, 'Bob')

    def test_query_returns_dataframe(self, tmp_path, monkeypatch):
        """Query method returns a pandas DataFrame."""
        monkeypatch.setattr(
            'src.utils.db_connection.project_root',
            tmp_path,
        )

        db_dir = tmp_path / 'src' / 'duckdb_databases'
        db_dir.mkdir(parents=True)

        config = make_config_dict(update_type='s3')
        config['draft_id'] = 'test_query_df'

        with get_duckdb(config) as db:
            db.execute('CREATE TABLE df_test (id INTEGER, value DOUBLE)')
            db.execute('INSERT INTO df_test VALUES (1, 3.14), (2, 2.71)')
            df = db.query('SELECT * FROM df_test ORDER BY id')

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ['id', 'value']

    def test_connection_closes_after_context(self, tmp_path, monkeypatch):
        """Connection is closed when exiting context."""
        monkeypatch.setattr(
            'src.utils.db_connection.project_root',
            tmp_path,
        )

        db_dir = tmp_path / 'src' / 'duckdb_databases'
        db_dir.mkdir(parents=True)

        config = make_config_dict(update_type='s3')
        config['draft_id'] = 'ctx_close_test'

        with get_duckdb(config) as db:
            captured_db = db

        with pytest.raises(duckdb.ConnectionException):
            captured_db.connection.query('SELECT 1')

    def test_closes_on_exception(self, tmp_path, monkeypatch):
        """Connection is closed even when exception occurs."""
        monkeypatch.setattr(
            'src.utils.db_connection.project_root',
            tmp_path,
        )

        db_dir = tmp_path / 'src' / 'duckdb_databases'
        db_dir.mkdir(parents=True)

        config = make_config_dict(update_type='s3')
        config['draft_id'] = 'ctx_exception_test'

        captured_db = None

        with pytest.raises(RuntimeError):
            with get_duckdb(config) as db:
                captured_db = db
                raise RuntimeError('Test error')

        with pytest.raises(duckdb.ConnectionException):
            captured_db.connection.query('SELECT 1')


class TestS3Configuration:
    """Tests for S3/DigitalOcean Spaces configuration."""

    def test_s3_credentials_passed_to_duckdb(self, tmp_path, monkeypatch):
        """S3 credentials are passed to eftoolkit.sql.DuckDB."""
        monkeypatch.setenv('TEST_S3_KEY_ID', 'test_key_id')
        monkeypatch.setenv('TEST_S3_SECRET', 'test_secret_key')
        monkeypatch.setattr(
            'src.utils.db_connection.project_root',
            tmp_path,
        )

        db_dir = tmp_path / 'src' / 'duckdb_databases'
        db_dir.mkdir(parents=True)

        config = make_config_dict(update_type='s3')
        config['draft_id'] = 's3_creds_test'

        db = get_duckdb(config)

        # eftoolkit creates an S3FileSystem when credentials are provided
        assert db.s3 is not None
        db.close()

    def test_works_without_s3_credentials(self, tmp_path, monkeypatch):
        """Connection works without S3 credentials."""
        monkeypatch.setattr(
            'src.utils.db_connection.project_root',
            tmp_path,
        )

        db_dir = tmp_path / 'src' / 'duckdb_databases'
        db_dir.mkdir(parents=True)

        config = make_config_dict(update_type='web')
        config['draft_id'] = 'no_s3_test'

        with get_duckdb(config) as db:
            result = db.connection.query('SELECT 1 + 1 as result').fetchall()

        assert result == [(2,)]
