import pytest
from unittest import mock
import os
from bottle import LocalRequest
from metrics_local import (
    process_json_values,
    generate_filename,
    create_log_directory,
    write_to_log_file,
    DATA_ROOT_PATH,
    PATH_MAP,
    save_request
)

def test_process_json_values_valid_json():
    request_mock = mock.Mock()
    request_mock.params = mock.MagicMock()
    request_mock.params.get.return_value = '{"test": "value"}'
    assert process_json_values(request_mock) == True

def test_process_json_values_invalid_json():
    request_mock = mock.Mock()
    request_mock.params = mock.MagicMock()
    request_mock.params.get.return_value = '{invalid json}'
    assert process_json_values(request_mock) == False

def test_generate_filename():
    request_mock = mock.Mock()
    request_mock.params.get.side_effect = lambda k, default=None: "test_value" if k in ["device_id", "timestamp"] else default
    filename = generate_filename(request_mock)
    assert filename == "log-test_value-test_value.json"

def test_create_log_directory(tmp_path):
    app_dir = os.path.join(tmp_path, "test_app",  "received")

    expected_path = os.path.join(app_dir, "received")
    returned_path = create_log_directory(app_dir)

    # Assert that the function returns the correct path
    assert returned_path == expected_path

    # Assert that the directory was actually created
    assert os.path.isdir(expected_path)

def test_write_to_log_file_success(tmp_path):
    log_path = tmp_path / "test.log"
    assert write_to_log_file(str(log_path), "Test content") == True
    with open(log_path, "r") as f:
        assert f.read() == "Test content"

def test_write_to_log_file_failure(tmp_path):
    log_path = tmp_path / "non_existent_directory" / "test.log"
    assert write_to_log_file(str(log_path), "Test content") == False

def make_mock_request(json_values={}, device_id="TestDevice", timestamp="123456"):
    request = LocalRequest({'wsgi.input': '', 'REQUEST_METHOD': 'POST'})
    request.params = json_values
    request.params['device_id'] = device_id
    request.params['timestamp'] = timestamp
    return request

@mock.patch('metrics_local.os.makedirs')
@mock.patch('metrics_local.open', new_callable=mock.mock_open, read_data="data")
def test_save_request_success(mock_open, mock_makedirs):
    path = "test_path"
    request = make_mock_request({"events": '{"key": "value"}'})
    PATH_MAP[path] = "test_app"

    with mock.patch('metrics_local.process_json_values', return_value=True), \
         mock.patch('metrics_local.generate_filename', return_value="log-file.json"), \
         mock.patch('metrics_local.write_to_log_file', return_value=True):
        
        assert save_request(path, request) == True
        mock_makedirs.assert_called_once_with(os.path.join(DATA_ROOT_PATH, "test_app/received"), exist_ok=True)

def test_save_request_invalid_json():
    request = make_mock_request({"events": 'invalid json'})
    path = "test_path"
    PATH_MAP[path] = "test_app"

    with mock.patch('metrics_local.process_json_values', return_value=False):
        assert save_request(path, request) == False

def test_save_request_invalid_path():
    request = make_mock_request()
    path = "invalid_path"
    assert save_request(path, request) == False

@mock.patch('metrics_local.os.makedirs', side_effect=OSError)
def test_save_request_dir_creation_fail(mock_makedirs):
    path = "test_path"
    request = make_mock_request()
    PATH_MAP[path] = "test_app"

    with mock.patch('metrics_local.process_json_values', return_value=True), \
         mock.patch('metrics_local.generate_filename', return_value="log-file.json"):
        
        assert save_request(path, request) == False
        mock_makedirs.assert_called_once_with(os.path.join(DATA_ROOT_PATH, "test_app/received"), exist_ok=True)