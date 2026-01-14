from unittest.mock import MagicMock, patch

import pandas as pd

from tests.conftest import make_config_dict


def test_table_to_df_returns_dataframe_from_query():
    """Query result is returned as a pandas DataFrame."""
    config = make_config_dict(update_type='s3')
    config['draft_id'] = 'test_catalog'

    mock_df = pd.DataFrame({'col1': [1, 2], 'col2': ['a', 'b']})
    mock_db = MagicMock()
    mock_db.query.return_value = mock_df

    with patch('src.utils.query.get_duckdb') as mock_get_duckdb:
        mock_get_duckdb.return_value.__enter__.return_value = mock_db
        mock_get_duckdb.return_value.__exit__.return_value = None

        from src.utils.query import table_to_df

        result = table_to_df(config, 'schema.table_name')

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2
    mock_db.query.assert_called_once_with('select * from test_catalog.schema.table_name')


def test_table_to_df_renames_columns_when_provided():
    """Columns are renamed when column list is provided."""
    config = make_config_dict(update_type='s3')
    config['draft_id'] = 'rename_test'

    mock_df = pd.DataFrame({'old1': [1, 2], 'old2': [3, 4]})
    mock_db = MagicMock()
    mock_db.query.return_value = mock_df

    with patch('src.utils.query.get_duckdb') as mock_get_duckdb:
        mock_get_duckdb.return_value.__enter__.return_value = mock_db
        mock_get_duckdb.return_value.__exit__.return_value = None

        from src.utils.query import table_to_df

        result = table_to_df(config, 'schema.table', columns=['New1', 'New2'])

    assert list(result.columns) == ['New1', 'New2']


def test_table_to_df_replaces_positive_infinity_with_none():
    """Positive infinity values are replaced with None."""
    config = make_config_dict(update_type='s3')
    config['draft_id'] = 'inf_test'

    mock_df = pd.DataFrame({'value': [1.0, float('inf'), 3.0]})
    mock_db = MagicMock()
    mock_db.query.return_value = mock_df

    with patch('src.utils.query.get_duckdb') as mock_get_duckdb:
        mock_get_duckdb.return_value.__enter__.return_value = mock_db
        mock_get_duckdb.return_value.__exit__.return_value = None

        from src.utils.query import table_to_df

        result = table_to_df(config, 'schema.table')

    assert result['value'].iloc[0] == 1.0
    assert result['value'].iloc[1] is None
    assert result['value'].iloc[2] == 3.0


def test_table_to_df_replaces_negative_infinity_with_none():
    """Negative infinity values are replaced with None."""
    config = make_config_dict(update_type='s3')
    config['draft_id'] = 'neg_inf_test'

    mock_df = pd.DataFrame({'value': [float('-inf'), 2.0]})
    mock_db = MagicMock()
    mock_db.query.return_value = mock_df

    with patch('src.utils.query.get_duckdb') as mock_get_duckdb:
        mock_get_duckdb.return_value.__enter__.return_value = mock_db
        mock_get_duckdb.return_value.__exit__.return_value = None

        from src.utils.query import table_to_df

        result = table_to_df(config, 'schema.table')

    assert result['value'].iloc[0] is None
    assert result['value'].iloc[1] == 2.0


def test_table_to_df_replaces_nan_with_none():
    """NaN values are replaced with None."""
    config = make_config_dict(update_type='s3')
    config['draft_id'] = 'nan_test'

    mock_df = pd.DataFrame({'value': [1.0, float('nan'), 3.0]})
    mock_db = MagicMock()
    mock_db.query.return_value = mock_df

    with patch('src.utils.query.get_duckdb') as mock_get_duckdb:
        mock_get_duckdb.return_value.__enter__.return_value = mock_db
        mock_get_duckdb.return_value.__exit__.return_value = None

        from src.utils.query import table_to_df

        result = table_to_df(config, 'schema.table')

    assert result['value'].iloc[0] == 1.0
    assert result['value'].iloc[1] is None
    assert result['value'].iloc[2] == 3.0


def test_table_to_df_handles_empty_dataframe():
    """Empty DataFrame is returned correctly."""
    config = make_config_dict(update_type='s3')
    config['draft_id'] = 'empty_test'

    mock_df = pd.DataFrame({'col': []})
    mock_db = MagicMock()
    mock_db.query.return_value = mock_df

    with patch('src.utils.query.get_duckdb') as mock_get_duckdb:
        mock_get_duckdb.return_value.__enter__.return_value = mock_db
        mock_get_duckdb.return_value.__exit__.return_value = None

        from src.utils.query import table_to_df

        result = table_to_df(config, 'schema.table')

    assert len(result) == 0


def test_table_to_df_uses_draft_id_as_catalog():
    """draft_id from config is used as the catalog name in query."""
    config = make_config_dict(update_type='s3')
    config['draft_id'] = 'my_catalog_name'

    mock_df = pd.DataFrame({'x': [1]})
    mock_db = MagicMock()
    mock_db.query.return_value = mock_df

    with patch('src.utils.query.get_duckdb') as mock_get_duckdb:
        mock_get_duckdb.return_value.__enter__.return_value = mock_db
        mock_get_duckdb.return_value.__exit__.return_value = None

        from src.utils.query import table_to_df

        table_to_df(config, 'dashboards.scoreboard')

    mock_db.query.assert_called_once_with(
        'select * from my_catalog_name.dashboards.scoreboard'
    )


def test_table_to_df_columns_none_preserves_original_names():
    """When columns is None, original column names are preserved."""
    config = make_config_dict(update_type='s3')
    config['draft_id'] = 'preserve_test'

    mock_df = pd.DataFrame({'original_a': [1], 'original_b': [2]})
    mock_db = MagicMock()
    mock_db.query.return_value = mock_df

    with patch('src.utils.query.get_duckdb') as mock_get_duckdb:
        mock_get_duckdb.return_value.__enter__.return_value = mock_db
        mock_get_duckdb.return_value.__exit__.return_value = None

        from src.utils.query import table_to_df

        result = table_to_df(config, 'schema.table', columns=None)

    assert list(result.columns) == ['original_a', 'original_b']


def test_table_to_df_passes_config_to_get_duckdb():
    """Config dict is passed to get_duckdb."""
    config = make_config_dict(update_type='s3')
    config['draft_id'] = 'config_pass_test'

    mock_df = pd.DataFrame({'x': [1]})
    mock_db = MagicMock()
    mock_db.query.return_value = mock_df

    with patch('src.utils.query.get_duckdb') as mock_get_duckdb:
        mock_get_duckdb.return_value.__enter__.return_value = mock_db
        mock_get_duckdb.return_value.__exit__.return_value = None

        from src.utils.query import table_to_df

        table_to_df(config, 'schema.table')

    mock_get_duckdb.assert_called_once_with(config)
