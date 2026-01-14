import os
import subprocess
from pathlib import Path

import pytest

from src import sqlmesh_project_dir, sqlmesh_test_config_path, sqlmesh_tests_dir

skip_sqlmesh = pytest.mark.skipif(
    os.environ.get('SKIP_SQLMESH_TESTS', '').lower() in ('1', 'true', 'yes'),
    reason='SKIP_SQLMESH_TESTS environment variable is set',
)


def get_test_files() -> list[Path]:
    """Get all YAML test files in the SQLMesh tests directory."""
    return sorted(sqlmesh_tests_dir.glob('test_*.yaml'))


def get_test_names_from_file(test_file: Path) -> list[str]:
    """Extract individual test names from a YAML test file."""
    import yaml

    with open(test_file) as f:
        content = yaml.safe_load(f)

    if content is None:
        return []
    return list(content.keys())


def generate_test_params() -> list[tuple[Path, str]]:
    """Generate pytest parameters for all SQLMesh tests."""
    params = []
    for test_file in get_test_files():
        for test_name in get_test_names_from_file(test_file):
            params.append((test_file, test_name))
    return params


@skip_sqlmesh
@pytest.mark.integration
@pytest.mark.parametrize(
    'test_file,test_name',
    generate_test_params(),
    ids=lambda x: x if isinstance(x, str) else x.stem,
)
def test_sqlmesh_model(test_file: Path, test_name: str):
    """Run a single SQLMesh unit test."""
    # Make the test file path relative to the SQLMesh project directory
    relative_test_file = test_file.relative_to(sqlmesh_project_dir)
    test_spec = f'{relative_test_file}::{test_name}'
    env = os.environ.copy()
    env['CONFIG_PATH'] = str(sqlmesh_test_config_path.resolve())
    result = subprocess.run(
        ['uv', 'run', 'sqlmesh', 'test', test_spec],
        cwd=sqlmesh_project_dir,
        capture_output=True,
        text=True,
        env=env,
    )

    if result.returncode != 0:
        pytest.fail(
            f'SQLMesh test failed: {test_name}\n'
            f'stdout: {result.stdout}\n'
            f'stderr: {result.stderr}'
        )


@skip_sqlmesh
@pytest.mark.integration
def test_sqlmesh_tests_exist():
    """Verify that SQLMesh test files exist."""
    test_files = get_test_files()

    assert len(test_files) > 0, 'No SQLMesh test files found'


@skip_sqlmesh
@pytest.mark.integration
def test_sqlmesh_project_valid():
    """Verify the SQLMesh project is valid by checking config."""
    config_file = sqlmesh_project_dir / 'config.py'

    assert config_file.exists(), 'SQLMesh config.py not found'
