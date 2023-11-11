import pytest
import asyncio
import aiofiles
import hashlib
import os

from unittest.mock import MagicMock, patch

from hitchhiker_source import FileManager


@pytest.fixture
def file_manager(tmp_path):
    # Use pytest's tmp_path fixture for a temporary file directory
    return FileManager(str(tmp_path))

@pytest.mark.asyncio
async def test_list_received_files(file_manager, mocker):
    # Mock os.listdir to return a list of filenames
    mocker.patch('os.listdir', return_value=['file1.txt', 'file2.txt'])

    # Mock os.path.isfile to always return True
    mocker.patch('os.path.isfile', return_value=True)

    files = await file_manager.list_received_files()
    assert len(files) == 2
    assert 'file1.txt' in files[0]
    assert 'file2.txt' in files[1]

@pytest.mark.asyncio
async def test_delete_file(file_manager, mocker):
    # Mock os.remove
    mocker.patch('os.remove')

    # Mock os.path.exists to always return True
    mocker.patch('os.path.exists', return_value=True)

    await file_manager.delete_file('file1.txt')
    os.remove.assert_called_once_with(file_manager.base_directory + '/file1.txt')

@pytest.mark.asyncio
async def test_file_info(file_manager, mocker):
    file_name = 'file1.txt'
    file_content = b'file_content'
    expected_md5_sum = hashlib.md5(file_content).hexdigest()

    # Mock read_file method of FileManager
    mocker.patch.object(file_manager, 'read_file', return_value=file_content)

    file_info = await file_manager.file_info(file_name, hydrate_blob=True)
    assert file_info.filename == file_name
    assert file_info.fileid == expected_md5_sum
    assert file_info.blob == file_content
