# box-office-drafting

> Automated box office draft tracking and scoring system that processes draft picks, calculates revenue-based scores, and updates Google Sheets with a dashboard.

## Features

- **Multi-league support**: Run multiple drafts from separate configuration files
- **Flexible data sources**: Read box office data from S3 parquet files or scrape from Box Office Mojo
- **Automated scoring**: Calculate scored revenue with round and movie multipliers
- **Google Sheets integration**: Automatically update formatted dashboards with rankings, scoreboards, and worst picks
- **Scheduled updates**: Daily automated sync via [Modal](https://modal.com/)

## How It Works

1. **Data ingestion**: Loads draft picks, multipliers, and exclusions from Google Sheets
2. **Box office data**: Fetches revenue data from S3 or scrapes Box Office Mojo
3. **Scoring**: Calculates scored revenue using multipliers and applies draft rules
4. **Dashboard generation**: Produces scoreboards, rankings, and "better pick" analysis
5. **Sheet updates**: Writes formatted results to Google Sheets with conditional formatting

## Configuration

Create a YAML configuration file in `src/config/` for each draft:

```yaml
name: 2025 Fantasy Box Office Standings
year: 2025
update_type: s3
sheet_name: 2025 Fantasy Box Office Draft
gspread_credentials_name: GSPREAD_CREDENTIALS
database_file: friends_2025.duckdb
bucket: box-office-tracking
s3_access_key_id_var_name: S3_ACCESS_KEY_ID
s3_secret_access_key_var_name: S3_SECRET_ACCESS_KEY
```

### Required Fields

- `year`: Draft year (current or previous year)
- `name`: Display name for the dashboard
- `sheet_name`: Google Sheet name to update
- `database_file`: DuckDB database filename (must end with `.duckdb`)
- `update_type`: Data source (`s3` or `web`)
- `gspread_credentials_name`: Environment variable name for Google Sheets credentials

### Optional Fields

- `bucket`: S3 bucket name (required if `update_type` is `s3`)
- `s3_access_key_id_var_name`: S3 access key ID env var name (required if `update_type` is `s3`)
- `s3_secret_access_key_var_name`: S3 secret access key env var name (required if `update_type` is `s3`)

### Environment Variables

The script automatically sets `CONFIG_PATH` for each config file. You need to set environment variables with the names specified in your configuration file:

- **Google Sheets credentials**: Set an environment variable with the name from `gspread_credentials_name` in your config. The value should be the Google Sheets service account credentials JSON string. These credentials must have read access to the Google Sheet specified in `sheet_name`.

- **S3 credentials** (if `update_type` is `s3`): Set environment variables with the names from `s3_access_key_id_var_name` and `s3_secret_access_key_var_name` in your config. These credentials must have read access to the S3 bucket specified in `bucket`.

I recommend using a .env file to set these environment variables.

Example (for the .env file):
```
GSPREAD_CREDENTIALS='{"type":"service_account",...}'
S3_ACCESS_KEY_ID='your-access-key-id'
S3_SECRET_ACCESS_KEY='your-secret-access-key'
```

## Usage

### Local Development

```bash
# Run locally
uv run python3 app.py
```

### Deployment

The application runs on Modal with daily scheduled updates at 9 AM UTC. All config files in `src/config/` are automatically discovered and processed.

### Deployment

```bash
uv run modal deploy app.py
```
