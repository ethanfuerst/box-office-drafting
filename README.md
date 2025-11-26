# box-office-drafting

Automated box office draft tracking and scoring system that processes draft picks, calculates revenue-based scores, and updates Google Sheets dashboards. Designed to work with `box-office-tracking` S3 tables or directly with Box Office Mojo.

## Features

- Multi-league support via separate config files
- Flexible data sources (S3 Parquet or live web scrape)
- Automated scoring with round and movie multipliers
- Google Sheets dashboards (rankings, scoreboards, worst picks, “better picks”)
- Daily scheduled sync via [Modal](https://modal.com/)

## How It Works

1. **Data ingestion** - Loads draft picks, multipliers, and exclusions from Google Sheets.
2. **Box office data** - Reads revenues from S3 (published tables from `box-office-tracking`) or scrapes Box Office Mojo.
3. **Scoring** - Applies draft rules and multipliers to compute scored revenue.
4. **Dashboard generation** - Builds standings, scoreboards, and “better pick” analysis.
5. **Sheet updates** - Writes formatted results back to Google Sheets.

## Installation

```bash
git clone https://github.com/your-org/box-office-drafting.git
cd box-office-drafting
uv sync
```

## Configuration
Create a YAML configuration file in `src/config/` for each draft:

```yaml
name: 2025 Fantasy Box Office Standings
year: 2025
update_type: s3         # or "web"
sheet_name: 2025 Fantasy Box Office Draft
gspread_credentials_name: GSPREAD_CREDENTIALS
draft_id: friends_2025

# Required if `update_type` == "s3"
bucket: box-office-tracking
s3_access_key_id_var_name: S3_ACCESS_KEY_ID
s3_secret_access_key_var_name: S3_SECRET_ACCESS_KEY
```

### Required fields

- `year` - Draft year (typically current or previous year)
- `name` - Display name for the dashboard
- `sheet_name` - Google Sheet name to update
- `draft_id` - Unique identifier for the draft (used to create the database file as `{draft_id}.duckdb`)
- `update_type` - Data source: `s3` or `web`
- `gspread_credentials_name` - Environment variable name containing Google Sheets credentials JSON

### Optional / conditional fields
#### Used when `update_type: s3`

- `bucket` - S3 bucket name
- `s3_access_key_id_var_name` - Environment variable name for S3 access key ID
- `s3_secret_access_key_var_name` - Environment variable name for S3 secret access key

### Environment Variables
Set environment variables referenced in your config:

- `Google Sheets` - The environment variable specified by `gspread_credentials_name`, containing the service account credentials JSON with access to `sheet_name`.
- `S3` (if `update_type: s3`) - The environment variables specified by `s3_access_key_id_var_name` and `s3_secret_access_key_var_name`, containing AWS credentials that can read from `bucket`.

Example .env:

```env
GSPREAD_CREDENTIALS='{"type":"service_account",...}'
S3_ACCESS_KEY_ID='your-access-key-id'
S3_SECRET_ACCESS_KEY='your-secret-access-key'
```

## Usage

### Local development
Run the app locally for all configs in `src/config/`:

```bash
uv run python app.py
```

### Modal deployment
Deploy the scheduled job to Modal:

```bash
uv run modal deploy app.py
```

By default, the job is scheduled to run daily at 09:00 UTC. All config files in `src/config/` are automatically discovered and processed.

## Compatibility with box-office-tracking

When using `update_type: s3`, this project expects the published tables produced by `box-office-tracking`:
 - Each release of `box-office-drafting` targets a specific major version / S3 prefix from `box-office-tracking`.
 - See the release notes and README in `box-office-tracking` for the current published table locations and schema guarantees.

## Versioning
This project uses semantic versioning (MAJOR.MINOR.PATCH). Breaking changes to the scoring rules, config format, or tracking-data contract will bump the major version.

## License
This project is licensed under the MIT license. See LICENSE for details.
