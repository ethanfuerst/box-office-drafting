import os
from unittest.mock import MagicMock, patch

from tests.conftest import make_config_dict


def test_run_sqlmesh_plan_sets_config_path_env_var(tmp_path):
    """CONFIG_PATH environment variable is set from config dict."""
    config = make_config_dict(update_type='s3')
    config_path = tmp_path / 'config.yml'
    config['path'] = config_path

    mock_context = MagicMock()
    mock_plan = MagicMock()
    mock_context.plan.return_value = mock_plan

    with patch('src.etl.Context', return_value=mock_context):
        with patch.dict(os.environ, {}, clear=False):
            from src.etl import run_sqlmesh_plan

            run_sqlmesh_plan(config)

            assert os.environ['CONFIG_PATH'] == str(config_path)


def test_run_sqlmesh_plan_creates_context_with_correct_path(tmp_path):
    """SQLMesh Context is created with the sqlmesh_project path."""
    config = make_config_dict(update_type='s3')
    config['path'] = tmp_path / 'config.yml'

    mock_context = MagicMock()
    mock_plan = MagicMock()
    mock_context.plan.return_value = mock_plan

    with patch('src.etl.Context') as MockContext:
        MockContext.return_value = mock_context

        from src.etl import run_sqlmesh_plan

        run_sqlmesh_plan(config)

    MockContext.assert_called_once()
    call_kwargs = MockContext.call_args
    paths_arg = call_kwargs.kwargs.get('paths') or call_kwargs.args[0]

    assert 'sqlmesh_project' in str(paths_arg)


def test_run_sqlmesh_plan_calls_plan_and_apply(tmp_path):
    """SQLMesh plan is created and applied."""
    config = make_config_dict(update_type='s3')
    config['path'] = tmp_path / 'config.yml'

    mock_context = MagicMock()
    mock_plan = MagicMock()
    mock_context.plan.return_value = mock_plan

    with patch('src.etl.Context', return_value=mock_context):
        from src.etl import run_sqlmesh_plan

        run_sqlmesh_plan(config)

    mock_context.plan.assert_called_once()
    mock_context.apply.assert_called_once_with(mock_plan)


def test_run_sqlmesh_plan_calls_run_after_apply(tmp_path):
    """SQLMesh run is called after apply."""
    config = make_config_dict(update_type='s3')
    config['path'] = tmp_path / 'config.yml'

    mock_context = MagicMock()
    mock_plan = MagicMock()
    mock_context.plan.return_value = mock_plan

    call_order = []
    mock_context.apply.side_effect = lambda x: call_order.append('apply')
    mock_context.run.side_effect = lambda: call_order.append('run')

    with patch('src.etl.Context', return_value=mock_context):
        from src.etl import run_sqlmesh_plan

        run_sqlmesh_plan(config)

    assert call_order == ['apply', 'run']
