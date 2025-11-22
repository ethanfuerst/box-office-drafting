import yaml

from src.utils.config_types import ConfigDict, validate_config


def get_config_dict(config_path: str) -> ConfigDict:
    '''
    Load, parse, and validate a YAML configuration file.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        ConfigDict: Validated configuration dictionary.

    Raises:
        FileNotFoundError: If the config file doesn't exist.
        ValueError: If configuration validation fails.
        yaml.YAMLError: If YAML parsing fails.
    '''
    with open(config_path, 'r') as yaml_in:
        yaml_object = yaml.safe_load(yaml_in)

    if yaml_object is None:
        raise ValueError(f'Configuration file {config_path} is empty or invalid')

    return validate_config(yaml_object)
