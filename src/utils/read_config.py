from typing import Any, Dict

import yaml


def get_config_dict(config_path: str) -> Dict[str, Any]:
    '''Load and parse a YAML configuration file.'''
    with open(config_path, 'r') as yaml_in:
        yaml_object = yaml.safe_load(yaml_in)

    return yaml_object
