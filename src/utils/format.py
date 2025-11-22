import json
from typing import Any, Dict, List, Union


def remove_comments(obj: Union[Dict, List]) -> Union[Dict, List]:
    '''Remove comment keys (starting with '_comment') from a nested dictionary or list.'''
    if isinstance(obj, dict):
        return {
            k: remove_comments(v)
            for k, v in obj.items()
            if not k.startswith('_comment')
        }
    elif isinstance(obj, list):
        return [remove_comments(item) for item in obj]
    else:
        return obj


def load_format_config(file_path: str) -> Dict[str, Any]:
    '''Load a JSON format configuration file and remove comments.'''
    with open(file_path, 'r') as file:
        config = json.load(file)
    return remove_comments(config)
