# SQLMesh Unit Tests

This directory contains unit tests for the SQLMesh transformation models.

## Directory Structure

```
tests/
├── config.yaml                  # Test configuration for SQLMesh
├── fixtures/                    # CSV fixture files for reusable test data
│   ├── base_query_standard.csv
│   ├── better_pick_final_standard.csv
│   ├── base_query_for_scoreboard.csv
│   └── better_pick_int_for_worst_picks.csv
├── dashboard_specs/             # Screenshots as acceptance criteria
│   └── README.md
├── test_base_query.yaml         # Tests for combined.base_query model
├── test_scoreboard.yaml         # Tests for dashboards.scoreboard model
├── test_best_picks.yaml         # Tests for dashboards.best_picks model
├── test_worst_picks.yaml        # Tests for dashboards.worst_picks model
└── README.md
```

## Running Tests

### SQLMesh Native (from SQLMesh project directory)

```bash
cd src/dashboard/sqlmesh_project

# Run all tests
uv run sqlmesh test

# Run tests for a specific model
uv run sqlmesh test tests/test_scoreboard.yaml

# Run a specific test case
uv run sqlmesh test tests/test_scoreboard.yaml::test_scoreboard_aggregates_by_drafter
```

### Pytest Wrapper (from project root)

```bash
# Run all tests including SQLMesh tests
uv run pytest tests/test_sqlmesh_project.py -v

# Skip SQLMesh tests for faster local runs
SKIP_SQLMESH_TESTS=1 uv run pytest

# Run only integration tests
uv run pytest -m integration -v

# Run all tests except integration
uv run pytest -m "not integration"
```

## Fixture Strategy

### File-Based Fixtures (Preferred)

For reusable test data, use CSV files in the `fixtures/` directory:

```yaml
test_with_csv_fixture:
  model: dashboards.scoreboard
  inputs:
    combined.base_query:
      format: csv
      path: tests/fixtures/base_query_for_scoreboard.csv
  outputs:
    query:
      rows:
        - drafted_by_name: Alice
          scored_revenue: 230000000
```

### Inline Fixtures

For simple, one-off test cases, inline YAML rows are fine:

```yaml
test_with_inline_data:
  model: dashboards.scoreboard
  inputs:
    combined.base_query:
      rows:
        - title: Movie A
          drafted_by: Alice
          scored_revenue: 100000000
```

## Test Format

Each test file is a YAML file containing one or more test cases:

```yaml
test_name:
  model: <model_name>           # Required: SQLMesh model to test
  description: <what it tests>  # Required: Human-readable description
  inputs:                       # Required: Mock data for upstream models
    <upstream_model>:
      rows:                     # Inline data
        - col1: val1
          col2: val2
      # OR
      format: csv               # File-based data
      path: tests/fixtures/file.csv
  outputs:                      # Required: Expected results
    query:
      rows:
        - col1: expected_val1
    partial: true               # Optional: Only check specified columns
```

### Partial Output Testing

Use `partial: true` when you only care about specific columns:

```yaml
outputs:
  partial: true
  query:
    rows:
      - title: Movie A
        scored_revenue: 100000000
      # Other columns are ignored
```

## Models Under Test

### Dashboard Models (Gold Layer)

| Model | Purpose | Key Columns |
|-------|---------|-------------|
| `dashboards.scoreboard` | Aggregates by drafter | `scored_revenue`, `num_released`, `correctly_drafted_pick_count` |
| `dashboards.best_picks` | Picks that outperformed | `positions_gained`, `actual_revenue` |
| `dashboards.worst_picks` | Picks with missed opportunity | `missed_revenue`, `number_of_better_picks` |

### Combined Models

| Model | Purpose | Key Columns |
|-------|---------|-------------|
| `combined.base_query` | Joins with better pick data | `rank`, `better_pick_title`, `still_in_theaters` |

## Adding Dashboard-Driven Tests

1. Take a screenshot of the dashboard and save to `dashboard_specs/`
2. Create CSV fixtures in `fixtures/` that produce the displayed values
3. Write test assertions matching the screenshot:

```yaml
test_dashboard_scenario:
  model: dashboards.scoreboard
  description: Matches dashboard screenshot scoreboard_example.png
  inputs:
    combined.base_query:
      format: csv
      path: tests/fixtures/dashboard_scenario.csv
  outputs:
    query:
      rows:
        - drafted_by_name: Alice
          scored_revenue: 230000000  # Matches screenshot
        - drafted_by_name: Bob
          scored_revenue: 180000000  # Matches screenshot
```

## Handling Time-Dependent Logic

For models using `today()` or date comparisons, tests should use deterministic fixture data:

```yaml
test_still_in_theaters_logic:
  model: combined.base_query
  inputs:
    combined.base_query_int:
      rows:
        - title: Recent Movie
          first_seen_date: 2024-12-01  # Use explicit dates
          still_in_theaters: true
```

## Test Coverage Summary

| Test File | Model | Test Count | Coverage |
|-----------|-------|------------|----------|
| `test_base_query.yaml` | `combined.base_query` | 4 | Joins, exclusions, formatting, ordering |
| `test_scoreboard.yaml` | `dashboards.scoreboard` | 4 | Aggregation, exclusions, correct picks, ordering |
| `test_best_picks.yaml` | `dashboards.best_picks` | 6 | Positions gained, exclusions, empty results |
| `test_worst_picks.yaml` | `dashboards.worst_picks` | 4 | Missed revenue, better pick counts, empty results |

**Total: 18 test cases covering 4 models**
