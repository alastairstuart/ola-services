import pytest
from unittest.mock import AsyncMock
from hitchhiker_source import HitchhikerSource, FileManager, SOURCE_ID
import hitchhiker_pb2
from google.protobuf.empty_pb2 import Empty

@pytest.fixture
def mock_file_manager(mocker):
    mock = mocker.Mock(FileManager, autospec=True)
    mock.list_received_files = AsyncMock()
    mock.read_file = AsyncMock()
    mock.delete_file = AsyncMock()
    mock.file_info = AsyncMock()
    return mock

@pytest.fixture
def hitchhiker_source(mock_file_manager):
    return HitchhikerSource(mock_file_manager)

@pytest.mark.asyncio
async def test_GetSourceId(hitchhiker_source):
    # Create a mock stream object
    mock_stream = AsyncMock()

    # Call the method
    await hitchhiker_source.GetSourceId(mock_stream)

    # Assert the behavior
    mock_stream.send_message.assert_called_once_with(hitchhiker_pb2.SourceId(id=SOURCE_ID))

@pytest.mark.asyncio
async def test_GetDownloads(hitchhiker_source, mock_file_manager):
    # Mock data
    mock_files = [hitchhiker_pb2.File(fileid="1", filename="file1.txt")]
    mock_file_manager.file_info.return_value = mock_files[0]
    mock_file_manager.list_received_files.return_value = ["file1.txt"]

    # Create a mock stream object
    mock_stream = AsyncMock()
    mock_stream.recv_message.return_value = AsyncMock(destinationId="dest1", clientId="client1")

    # Call the method
    await hitchhiker_source.GetDownloads(mock_stream)

    # Assert the behavior
    mock_stream.send_message.assert_called_once_with(hitchhiker_pb2.FileList(files=mock_files))

@pytest.mark.asyncio
async def test_DownloadFile(hitchhiker_source, mock_file_manager):
    # Mock data
    mock_file_info = hitchhiker_pb2.File(fileid="1", filename="file1.txt", blob=b"content")
    mock_file_manager.file_info.return_value = mock_file_info

    # Create a mock stream object
    mock_stream = AsyncMock()
    mock_stream.recv_message.return_value = AsyncMock(files=[hitchhiker_pb2.File(filename="file1.txt")])

    # Call the method
    await hitchhiker_source.DownloadFile(mock_stream)

    # Assert the behavior
    mock_stream.send_message.assert_called_once_with(mock_file_info)

@pytest.mark.asyncio
async def test_MarkDelivered(hitchhiker_source, mock_file_manager):
    # Create a mock stream object
    mock_stream = AsyncMock()
    mock_stream.recv_message.return_value = AsyncMock(files=[hitchhiker_pb2.File(filename="file1.txt")])

    # Call the method
    await hitchhiker_source.MarkDelivered(mock_stream)

    # Assert the behavior
    mock_file_manager.delete_file.assert_called_once_with("file1.txt")
    mock_stream.send_message.assert_called_once_with(Empty())