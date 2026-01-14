from pathlib import Path

project_root = Path(__file__).parent.parent
sqlmesh_project_dir = project_root / 'src' / 'dashboard' / 'sqlmesh_project'
sqlmesh_models_dir = sqlmesh_project_dir / 'models'
sqlmesh_tests_dir = sqlmesh_project_dir / 'tests'
sqlmesh_test_config_path = sqlmesh_tests_dir / 'config.yaml'
