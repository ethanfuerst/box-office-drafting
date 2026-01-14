# Dashboard Specifications

This directory contains screenshots of dashboards that serve as acceptance criteria for SQLMesh tests.

## Purpose

When adding new SQLMesh tests for dashboard models, use screenshots from the live dashboard as the specification:

1. Take a screenshot of the dashboard table/metric you want to test
2. Save it in this directory with a descriptive name (e.g., `scoreboard_example.png`)
3. Create fixture data that would produce the values shown in the screenshot
4. Write test assertions that verify those expected values

## Naming Convention

- `scoreboard_*.png` - Screenshots of the scoreboard dashboard
- `best_picks_*.png` - Screenshots of the best picks table
- `worst_picks_*.png` - Screenshots of the worst picks table

## Using Screenshots as Specs

### Example Workflow

1. Screenshot shows Alice with $230M scored revenue
2. Create fixtures in `fixtures/` that sum to $230M for Alice
3. Add test case asserting `scored_revenue: 230000000` for Alice

### Key Metrics to Verify

**Scoreboard:**
- `scored_revenue` - Total adjusted revenue per drafter
- `num_released` - Count of movies with revenue > 0
- `correctly_drafted_pick_count` - Movies with no better pick available
- `correct_pick_pct` - Ratio of correct picks to total picks

**Best Picks:**
- `positions_gained` - Draft position minus revenue rank
- `actual_revenue` - Unadjusted revenue

**Worst Picks:**
- `missed_revenue` - Best available pick revenue minus actual pick revenue
- `number_of_better_picks` - Count of movies that would have been better

## Current Screenshots

(Add screenshots here as you create dashboard-driven tests)
