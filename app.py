import modal

from src import project_root
from src.etl import google_sheet_sync
from src.utils.config import get_config_dict

app = modal.App('box-office-drafting')

modal_image = (
    modal.Image.debian_slim(python_version='3.12')
    .pip_install_from_pyproject('pyproject.toml')
    .add_local_file(
        'src/duckdb_databases/.gitkeep',
        remote_path='/root/src/duckdb_databases/.gitkeep',
        copy=True,
    )
    .add_local_dir('src/config/', remote_path='/root/src/config')
    .add_local_dir('src/assets/', remote_path='/root/src/assets')
    .add_local_dir(
        'src/dashboard/sqlmesh_project/',
        remote_path='/root/src/dashboard/sqlmesh_project',
    )
    .add_local_python_source('src')
)


@app.function(
    image=modal_image,
    schedule=modal.Cron('0 9 * * *'),
    secrets=[modal.Secret.from_name('box-office-drafting-secrets')],
    retries=modal.Retries(
        max_retries=3,
        backoff_coefficient=1.0,
        initial_delay=60.0,
    ),
)
def update_dashboards():
    '''Discover and sync all valid YAML config files in src/config/.'''
    config_dir = project_root / 'src' / 'config'
    config_files = sorted(config_dir.glob('*.yml'))
    print(
        f'Config files found: {", ".join([config_file.name for config_file in config_files])}'
    )

    if not config_files:
        print(f'No config files found in {config_dir}')
        return

    seen_draft_ids = {}

    for config_path in config_files:
        config_dict = get_config_dict(config_path)
        draft_id = config_dict['draft_id']

        if draft_id in seen_draft_ids:
            raise ValueError(
                f"draft_id '{draft_id}' is used in both {seen_draft_ids[draft_id].name} and {config_path.name}"
            )

        seen_draft_ids[draft_id] = config_path

        google_sheet_sync(config_dict=config_dict)


if __name__ == '__main__':
    update_dashboards.local()
