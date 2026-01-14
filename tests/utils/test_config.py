import pytest
import yaml

from src.utils.config import get_config_dict, read_config, validate_config
from tests.conftest import make_config_dict


def test_read_config_reads_valid_yaml_file(tmp_path):
    """Valid YAML file is parsed into a dictionary."""
    config_content = """
year: 2025
name: Test Draft
sheet_name: Test Sheet
draft_id: test_draft
update_type: web
gspread_credentials_name: TEST_CREDS
"""
    config_file = tmp_path / 'config.yml'
    config_file.write_text(config_content)

    result = read_config(config_file)

    assert result['year'] == 2025
    assert result['name'] == 'Test Draft'
    assert result['draft_id'] == 'test_draft'


def test_read_config_accepts_string_path(tmp_path):
    """Function accepts string path argument."""
    config_content = 'key: value'
    config_file = tmp_path / 'string_path.yml'
    config_file.write_text(config_content)

    result = read_config(str(config_file))

    assert result == {'key': 'value'}


def test_read_config_raises_file_not_found(tmp_path):
    """FileNotFoundError is raised for missing file."""
    missing_file = tmp_path / 'missing.yml'

    with pytest.raises(FileNotFoundError):
        read_config(missing_file)


def test_read_config_raises_value_error_on_empty_file(tmp_path):
    """ValueError is raised for empty config file."""
    empty_file = tmp_path / 'empty.yml'
    empty_file.write_text('')

    with pytest.raises(ValueError, match='empty or invalid'):
        read_config(empty_file)


def test_read_config_raises_value_error_on_yaml_null(tmp_path):
    """ValueError is raised when YAML parses to None."""
    null_file = tmp_path / 'null.yml'
    null_file.write_text('---\n')

    with pytest.raises(ValueError, match='empty or invalid'):
        read_config(null_file)


def test_read_config_raises_yaml_error_on_invalid_yaml(tmp_path):
    """YAMLError is raised for invalid YAML syntax."""
    invalid_file = tmp_path / 'invalid.yml'
    invalid_file.write_text('key: [unclosed bracket')

    with pytest.raises(yaml.YAMLError):
        read_config(invalid_file)


def test_validate_config_validates_complete_web_config(current_year):
    """Complete web config passes validation."""
    config = make_config_dict(year=current_year, update_type='web')

    result = validate_config(config)

    assert result['year'] == current_year
    assert result['update_type'] == 'web'


def test_validate_config_validates_complete_s3_config(current_year):
    """Complete S3 config with all required fields passes validation."""
    config = make_config_dict(year=current_year, update_type='s3')

    result = validate_config(config)

    assert result['update_type'] == 's3'
    assert 'bucket' in result
    assert 's3_access_key_id_var_name' in result
    assert 's3_secret_access_key_var_name' in result


def test_validate_config_accepts_previous_year(current_year):
    """Previous year is accepted as valid."""
    config = make_config_dict(year=current_year - 1, update_type='web')

    result = validate_config(config)

    assert result['year'] == current_year - 1


def test_validate_config_rejects_future_year(current_year):
    """Future year is rejected."""
    config = make_config_dict(year=current_year + 1, update_type='web')

    with pytest.raises(ValueError, match='year'):
        validate_config(config)


def test_validate_config_rejects_old_year(current_year):
    """Year older than previous year is rejected."""
    config = make_config_dict(year=current_year - 2, update_type='web')

    with pytest.raises(ValueError, match='year'):
        validate_config(config)


def test_validate_config_rejects_invalid_update_type(current_year):
    """Invalid update_type is rejected."""
    config = make_config_dict(year=current_year, update_type='invalid')

    with pytest.raises(ValueError, match='update_type'):
        validate_config(config)


def test_validate_config_rejects_missing_required_fields(current_year):
    """Missing required fields are reported."""
    config = {'year': current_year}

    with pytest.raises(ValueError, match='Missing required fields'):
        validate_config(config)


def test_validate_config_reports_multiple_missing_fields(current_year):
    """All missing fields are reported in error message."""
    config = {'year': current_year, 'name': 'Test'}

    with pytest.raises(ValueError) as exc_info:
        validate_config(config)

    error_msg = str(exc_info.value)

    assert 'sheet_name' in error_msg
    assert 'draft_id' in error_msg
    assert 'update_type' in error_msg


def test_validate_config_rejects_wrong_type_for_year(current_year):
    """Non-integer year is rejected."""
    config = make_config_dict(year=current_year, update_type='web')
    config['year'] = str(current_year)

    with pytest.raises(ValueError, match='year.*expected int'):
        validate_config(config)


def test_validate_config_rejects_wrong_type_for_name(current_year):
    """Non-string name is rejected."""
    config = make_config_dict(year=current_year, update_type='web')
    config['name'] = 123

    with pytest.raises(ValueError, match='name.*expected str'):
        validate_config(config)


def test_validate_config_s3_requires_bucket(current_year):
    """S3 update_type requires bucket field."""
    config = make_config_dict(year=current_year, update_type='web')
    config['update_type'] = 's3'
    config.pop('bucket', None)

    with pytest.raises(ValueError, match='bucket.*required'):
        validate_config(config)


def test_validate_config_s3_requires_access_key_var_name(current_year):
    """S3 update_type requires s3_access_key_id_var_name field."""
    config = make_config_dict(year=current_year, update_type='s3')
    del config['s3_access_key_id_var_name']

    with pytest.raises(ValueError, match='s3_access_key_id_var_name.*required'):
        validate_config(config)


def test_validate_config_s3_requires_secret_key_var_name(current_year):
    """S3 update_type requires s3_secret_access_key_var_name field."""
    config = make_config_dict(year=current_year, update_type='s3')
    del config['s3_secret_access_key_var_name']

    with pytest.raises(ValueError, match='s3_secret_access_key_var_name.*required'):
        validate_config(config)


def test_validate_config_web_does_not_require_s3_fields(current_year):
    """Web update_type does not require S3 fields."""
    config = make_config_dict(year=current_year, update_type='web')
    config.pop('bucket', None)
    config.pop('s3_access_key_id_var_name', None)
    config.pop('s3_secret_access_key_var_name', None)

    result = validate_config(config)

    assert result['update_type'] == 'web'


def test_get_config_dict_loads_validates_and_adds_path(tmp_path, current_year):
    """Config is loaded, validated, and path field is added."""
    config_content = f"""
year: {current_year}
name: Test Draft
sheet_name: Test Sheet
draft_id: test_draft
update_type: web
gspread_credentials_name: TEST_CREDS
"""
    config_file = tmp_path / 'full_config.yml'
    config_file.write_text(config_content)

    result = get_config_dict(config_file)

    assert result['year'] == current_year
    assert result['path'] == config_file


def test_get_config_dict_path_field_is_path_object(tmp_path, current_year):
    """The path field is a Path object."""
    from pathlib import Path

    config_content = f"""
year: {current_year}
name: Test
sheet_name: Sheet
draft_id: draft
update_type: web
gspread_credentials_name: CREDS
"""
    config_file = tmp_path / 'path_type.yml'
    config_file.write_text(config_content)

    result = get_config_dict(str(config_file))

    assert isinstance(result['path'], Path)


def test_get_config_dict_raises_on_invalid_config(tmp_path):
    """ValueError is raised for invalid config."""
    config_content = 'key: value'
    config_file = tmp_path / 'invalid_config.yml'
    config_file.write_text(config_content)

    with pytest.raises(ValueError, match='Missing required fields'):
        get_config_dict(config_file)


def test_get_config_dict_raises_on_empty_file(tmp_path):
    """ValueError is raised for empty file."""
    empty_file = tmp_path / 'empty_get.yml'
    empty_file.write_text('')

    with pytest.raises(ValueError, match='empty or invalid'):
        get_config_dict(empty_file)


def test_get_config_dict_loads_s3_config(tmp_path, current_year):
    """S3 config with all fields loads successfully."""
    config_content = f"""
year: {current_year}
name: S3 Draft
sheet_name: S3 Sheet
draft_id: s3_draft
update_type: s3
gspread_credentials_name: CREDS
bucket: my-bucket
s3_access_key_id_var_name: S3_KEY
s3_secret_access_key_var_name: S3_SECRET
"""
    config_file = tmp_path / 's3_config.yml'
    config_file.write_text(config_content)

    result = get_config_dict(config_file)

    assert result['update_type'] == 's3'
    assert result['bucket'] == 'my-bucket'
