#!/usr/bin/env python3
"""
SQLMesh Model Test Coverage Report.

Analyzes which SQLMesh models have test coverage and reports on gaps.

Usage:
    uv run python scripts/sqlmesh_coverage.py
"""

import re
from pathlib import Path

import yaml

from src import sqlmesh_models_dir, sqlmesh_tests_dir


def get_all_models() -> dict[str, list[str]]:
    """Get all SQLMesh models grouped by layer."""
    models_by_layer: dict[str, list[str]] = {}

    for layer_dir in sorted(sqlmesh_models_dir.iterdir()):
        if not layer_dir.is_dir() or layer_dir.name.startswith('.'):
            continue

        layer_name = layer_dir.name
        models_by_layer[layer_name] = []

        for model_file in sorted(layer_dir.glob('*.sql')):
            model_name = extract_model_name(model_file)
            if model_name:
                models_by_layer[layer_name].append(model_name)

        # Also check for Python models
        for model_file in sorted(layer_dir.glob('*.py')):
            if model_file.name.startswith('_'):
                continue
            model_name = extract_model_name_from_python(model_file)
            if model_name:
                models_by_layer[layer_name].append(model_name)

    return models_by_layer


def extract_model_name(sql_file: Path) -> str | None:
    """Extract model name from MODEL() declaration in SQL file."""
    content = sql_file.read_text()
    match = re.search(r'MODEL\s*\([^)]*name\s+([a-zA-Z_][a-zA-Z0-9_.]*)', content)
    if match:
        return match.group(1)
    return None


def extract_model_name_from_python(py_file: Path) -> str | None:
    """Extract model name from Python model file."""
    content = py_file.read_text()
    # Look for @model decorator or name= in model definition
    match = re.search(r'name\s*=\s*["\']([a-zA-Z_][a-zA-Z0-9_.]*)["\']', content)
    if match:
        return match.group(1)
    return None


def get_tested_models() -> dict[str, set[str]]:
    """Get all models that have tests, grouped by test file."""
    tested: dict[str, set[str]] = {}

    for test_file in sqlmesh_tests_dir.glob('test_*.yaml'):
        with open(test_file) as f:
            content = yaml.safe_load(f)

        if not content:
            continue

        tested[test_file.name] = set()
        for test_name, test_config in content.items():
            if isinstance(test_config, dict) and 'model' in test_config:
                tested[test_file.name].add(test_config['model'])

    return tested


def get_test_count_by_model() -> dict[str, int]:
    """Count number of tests per model."""
    counts: dict[str, int] = {}

    for test_file in sqlmesh_tests_dir.glob('test_*.yaml'):
        with open(test_file) as f:
            content = yaml.safe_load(f)

        if not content:
            continue

        for test_name, test_config in content.items():
            if isinstance(test_config, dict) and 'model' in test_config:
                model = test_config['model']
                counts[model] = counts.get(model, 0) + 1

    return counts


def print_coverage_report() -> tuple[int, int]:
    """Print coverage report and return (covered, total) counts."""
    models_by_layer = get_all_models()
    tested_by_file = get_tested_models()
    test_counts = get_test_count_by_model()

    # Flatten all tested models
    all_tested = set()
    for models in tested_by_file.values():
        all_tested.update(models)

    total_models = 0
    covered_models = 0

    print('=' * 70)
    print('SQLMesh Model Test Coverage Report')
    print('=' * 70)
    print()

    for layer, models in models_by_layer.items():
        layer_covered = sum(1 for m in models if m in all_tested)
        layer_total = len(models)
        total_models += layer_total
        covered_models += layer_covered

        pct = (layer_covered / layer_total * 100) if layer_total > 0 else 0
        print(f'{layer} ({layer_covered}/{layer_total} = {pct:.0f}%)')
        print('-' * 40)

        for model in models:
            if model in all_tested:
                test_count = test_counts.get(model, 0)
                print(f'  [x] {model} ({test_count} tests)')
            else:
                print(f'  [ ] {model}')
        print()

    # Summary
    overall_pct = (covered_models / total_models * 100) if total_models > 0 else 0
    print('=' * 70)
    print(f'TOTAL: {covered_models}/{total_models} models covered ({overall_pct:.0f}%)')
    print(f'       {sum(test_counts.values())} total test cases')
    print('=' * 70)

    # List test files
    print()
    print('Test Files:')
    for test_file, models in sorted(tested_by_file.items()):
        print(f'  {test_file}: {", ".join(sorted(models))}')

    return covered_models, total_models


def main():
    covered, total = print_coverage_report()

    # Exit with non-zero if coverage is below threshold (optional)
    # threshold = 0.5
    # if total > 0 and covered / total < threshold:
    #     sys.exit(1)


if __name__ == '__main__':
    main()
