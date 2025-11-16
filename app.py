import modal

from src import project_root
from src.etl import google_sheet_sync, s3_sync

app = modal.App('box-office-drafting')

modal_image = (
    modal.Image.debian_slim(python_version='3.13')
    .pip_install_from_pyproject('pyproject.toml')
    .add_local_dir('src/config/', remote_path='/root/src/config')
    .add_local_dir('src/assets/', remote_path='/root/src/assets')
    .add_local_python_source('src')
)


@app.function(
    image=modal_image,
    schedule=modal.Cron('0 4 * * *'),
    secrets=[modal.Secret.from_name('box-office-drafting-secrets')],
    retries=modal.Retries(
        max_retries=3,
        backoff_coefficient=1.0,
        initial_delay=60.0,
    ),
)
def run_s3_sync():
    s3_sync(config_path='config/boxofficemojo_2025.yaml')


@app.function(
    image=modal_image,
    schedule=modal.Cron('0 5 * * *'),
    secrets=[modal.Secret.from_name('box-office-drafting-secrets')],
    retries=modal.Retries(
        max_retries=3,
        backoff_coefficient=1.0,
        initial_delay=60.0,
    ),
)
def run_friends_2025_sync():
    google_sheet_sync(config_path='config/friends_2025.yaml')


@app.function(
    image=modal_image,
    schedule=modal.Cron('0 5 * * *'),
    secrets=[modal.Secret.from_name('box-office-drafting-secrets')],
    retries=modal.Retries(
        max_retries=3,
        backoff_coefficient=1.0,
        initial_delay=60.0,
    ),
)
def run_ethan_and_noah_2025_sync():
    google_sheet_sync(config_path='config/ethan_and_noah_2025.yaml')


if __name__ == '__main__':
    s3_sync(config_path=project_root / 'src/config/s3_sync.yml')
    google_sheet_sync(config_path=project_root / 'src/config/friends_config.yml')
    google_sheet_sync(config_path=project_root / 'src/config/ethan_noah_config.yml')
