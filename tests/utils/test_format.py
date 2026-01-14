import json

import pytest

from src.utils.format import load_format_config, remove_comments


def test_remove_comments_removes_top_level_comment_keys():
    """Comment keys at the top level are removed."""
    obj = {
        '_comment': 'This is a comment',
        'key1': 'value1',
        '_comment_another': 'Another comment',
        'key2': 'value2',
    }

    result = remove_comments(obj)

    assert result == {'key1': 'value1', 'key2': 'value2'}


def test_remove_comments_removes_nested_comment_keys():
    """Comment keys in nested dictionaries are removed."""
    obj = {
        'outer': {
            '_comment': 'Nested comment',
            'inner_key': 'inner_value',
        },
        'other': 'value',
    }

    result = remove_comments(obj)

    assert result == {'outer': {'inner_key': 'inner_value'}, 'other': 'value'}


def test_remove_comments_removes_comments_in_list_items():
    """Comment keys inside list items are removed."""
    obj = {
        'items': [
            {'_comment': 'Comment in list', 'name': 'item1'},
            {'name': 'item2'},
        ]
    }

    result = remove_comments(obj)

    assert result == {'items': [{'name': 'item1'}, {'name': 'item2'}]}


def test_remove_comments_handles_deeply_nested_structures():
    """Comment keys in deeply nested structures are removed."""
    obj = {
        'level1': {
            'level2': {
                'level3': {
                    '_comment': 'Deep comment',
                    'value': 42,
                }
            }
        }
    }

    result = remove_comments(obj)

    assert result == {'level1': {'level2': {'level3': {'value': 42}}}}


def test_remove_comments_preserves_non_comment_keys():
    """Keys not starting with '_comment' are preserved."""
    obj = {
        '_other': 'not a comment',
        'comment': 'also not a comment',
        '_comment': 'this is a comment',
    }

    result = remove_comments(obj)

    assert result == {'_other': 'not a comment', 'comment': 'also not a comment'}


def test_remove_comments_handles_empty_dict():
    """Empty dictionary returns empty dictionary."""
    result = remove_comments({})

    assert result == {}


def test_remove_comments_handles_empty_list():
    """Empty list returns empty list."""
    result = remove_comments([])

    assert result == []


def test_remove_comments_handles_list_of_dicts():
    """List of dictionaries has comments removed from each."""
    obj = [
        {'_comment': 'first', 'a': 1},
        {'_comment': 'second', 'b': 2},
    ]

    result = remove_comments(obj)

    assert result == [{'a': 1}, {'b': 2}]


def test_remove_comments_handles_mixed_list():
    """Lists with mixed types are processed correctly."""
    obj = [
        {'_comment': 'dict comment', 'key': 'value'},
        [{'_comment': 'nested list comment', 'nested': True}],
    ]

    result = remove_comments(obj)

    assert result == [{'key': 'value'}, [{'nested': True}]]


def test_load_format_config_loads_json_and_removes_comments(tmp_path):
    """JSON file is loaded and comments are removed."""
    config = {
        '_comment': 'This should be removed',
        'format_rule': {'bold': True},
    }
    config_file = tmp_path / 'format.json'
    config_file.write_text(json.dumps(config))

    result = load_format_config(config_file)

    assert result == {'format_rule': {'bold': True}}


def test_load_format_config_loads_nested_config(tmp_path):
    """Nested format configuration is loaded correctly."""
    config = {
        'A1:B2': {
            '_comment': 'Header formatting',
            'textFormat': {'bold': True, 'fontSize': 12},
        },
        'C1:D2': {
            'backgroundColor': {'red': 1, 'green': 0, 'blue': 0},
        },
    }
    config_file = tmp_path / 'nested_format.json'
    config_file.write_text(json.dumps(config))

    result = load_format_config(config_file)

    assert 'A1:B2' in result
    assert '_comment' not in result['A1:B2']
    assert result['A1:B2']['textFormat'] == {'bold': True, 'fontSize': 12}


def test_load_format_config_accepts_path_object(tmp_path):
    """Function accepts Path objects."""
    from pathlib import Path

    config = {'key': 'value'}
    config_file = tmp_path / 'path_test.json'
    config_file.write_text(json.dumps(config))
    path_obj = Path(config_file)

    result = load_format_config(path_obj)

    assert result == {'key': 'value'}


def test_load_format_config_accepts_string_path(tmp_path):
    """Function accepts string paths."""
    config = {'key': 'value'}
    config_file = tmp_path / 'string_test.json'
    config_file.write_text(json.dumps(config))
    string_path = str(config_file)

    result = load_format_config(string_path)

    assert result == {'key': 'value'}


def test_load_format_config_raises_on_missing_file(tmp_path):
    """FileNotFoundError is raised for missing files."""
    missing_file = tmp_path / 'does_not_exist.json'

    with pytest.raises(FileNotFoundError):
        load_format_config(missing_file)


def test_load_format_config_raises_on_invalid_json(tmp_path):
    """JSONDecodeError is raised for invalid JSON."""
    invalid_file = tmp_path / 'invalid.json'
    invalid_file.write_text('not valid json {{{')

    with pytest.raises(json.JSONDecodeError):
        load_format_config(invalid_file)


def test_load_format_config_handles_empty_json_object(tmp_path):
    """Empty JSON object returns empty dict."""
    config_file = tmp_path / 'empty.json'
    config_file.write_text('{}')

    result = load_format_config(config_file)

    assert result == {}
