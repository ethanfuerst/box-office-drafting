import modal

from src import project_root
from src.etl import google_sheet_sync

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
    google_sheet_sync(config_path=project_root / 'src/config/friends_2025.yml')
    google_sheet_sync(config_path=project_root / 'src/config/ethan_and_noah_2025.yml')


if __name__ == '__main__':
    update_dashboards.local()
