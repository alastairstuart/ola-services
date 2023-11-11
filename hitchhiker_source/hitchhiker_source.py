import argparse
from grpclib.server import Server
from grpclib.const import Status
from grpclib.exceptions import GRPCError
from google.protobuf.empty_pb2 import Empty
import asyncio
import aiofiles # used so we don't block the main thread
import hashlib
import logging
import os

# Assuming the generated Python code from the protobuf definition is in hitchhiker_pb2.py and hitchhiker_grpc.py
import hitchhiker_pb2
import hitchhiker_grpc

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

# Set up the command line argument parser
parser = argparse.ArgumentParser(description="Start the web server with specified data directory.")
default_log_root = os.environ.get('OLA_ML_DATA_ROOT', os.path.join(os.path.dirname(__file__), "../data"))
parser.add_argument('--data-root', type=str, default=default_log_root,
                    help='The directory path for log root (default: %(default)s)')
default_source_id = os.environ.get('OLA_HHS_SOURCE_ID', "pilot04")
parser.add_argument('--source-id', type=str, default=default_source_id,
                    help='The directory path for log root (default: %(default)s)')
args = parser.parse_args()


DATA_ROOT_PATH = args.data_root
# TODO Get smarter about this if we need to support other PATHs
METRICS_PATH = os.path.join(DATA_ROOT_PATH, "countly", "received")
SOURCE_ID = args.source_id

class FileManager:
    def __init__(self, base_directory):
        self.base_directory = base_directory

    async def list_received_files(self):
        path = self.base_directory
        return [os.path.join(path, file) for file in os.listdir(path) if os.path.isfile(os.path.join(path, file))]

    async def read_file(self, filename):
        filepath = os.path.join(self.base_directory, filename)
        async with aiofiles.open(filepath, 'rb') as file:
            content = await file.read()
        return content

    async def delete_file(self, filename):
        filepath = os.path.join(self.base_directory, filename)
        if os.path.exists(filepath):
            os.remove(filepath)  # os.remove is not async, but it's usually OK as it's a fast operation

    async def file_info(self, filepath, hydrate_blob=False):
        filename = os.path.basename(filepath)
        fileid = None
        blob = None

        content = await self.read_file(filename)
        # TODO Cache these somewhere sensible
        fileid = hashlib.md5(content).hexdigest()

        if hydrate_blob:
            blob = content

        return hitchhiker_pb2.File(
            fileid=fileid,
            filename=filename,
            type="application/json",  # Adjust the type as needed
            blob=blob
        )

class HitchhikerSource(hitchhiker_grpc.HitchhikerSourceBase):
    def __init__(self, file_manager):
        self.file_manager = file_manager

    async def GetSourceId(self, stream):
        logging.info(f"GetSourceId: Requested")
        await stream.send_message(hitchhiker_pb2.SourceId(id=SOURCE_ID))

    async def GetDownloads(self, stream):
        request = await stream.recv_message()

        logging.info(f"GetDownloads: Requested for destination \"{request.destinationId}\" by client \"{request.clientId}\"")

        try:
            received_files = await self.file_manager.list_received_files()
            files = [await self.file_manager.file_info(filepath, hydrate_blob=False) for filepath in received_files]
            await stream.send_message(hitchhiker_pb2.FileList(files=files))
        except FileNotFoundError:
            logging.error(f"GetDownloads: Directory not found")
            raise GRPCError(Status.NOT_FOUND, "Downloads not found")
        except PermissionError:
            logging.error("GetDownloads: Permission denied")
            raise GRPCError(Status.PERMISSION_DENIED, "Permission denied")
        except Exception as e:
            logging.error(f"GetDownloads: Unexpected error: {str(e)}")
            raise GRPCError(Status.INTERNAL, "Unexpected error")

    async def DownloadFile(self, stream):
        request = await stream.recv_message()

        for file_info in request.files:
            try:
                # Send the file back to the client
                await stream.send_message(await self.file_manager.file_info(file_info.filename, hydrate_blob=True))

            except FileNotFoundError:
                logging.warning(f"DownloadFile: File not found: {file_info.filename}")
                raise GRPCError(Status.NOT_FOUND, f"File not found: {file_info.filename}")

    async def MarkDelivered(self, stream):
        request = await stream.recv_message()

        # TODO As there's a destructive action here, do some sanity checking on the file path

        for file_info in request.files:
            try:
                await self.file_manager.delete_file(file_info.filename)
                logging.info(f"MarkDelivered: File deleted: \"{file_info.filename}\"")

            except FileNotFoundError:
                logging.warning(f"MarkDelivered: File to delete not found: \"{file_info.filename}\"")
                raise GRPCError(Status.NOT_FOUND, f"Downloads not found")

            except Exception as e:
                logging.error(f"MarkDelivered: Error deleting file \"{file_info.filename}\": {str(e)}")
                raise GRPCError(Status.INTERNAL, "Internal server error")

        await stream.send_message(Empty())

async def main():
    file_manager = FileManager(METRICS_PATH)
    server = Server([HitchhikerSource(file_manager)])
    await server.start('127.0.0.1', 50051)
    logging.info("HitchhikerSource service running...")
    await server.wait_closed()

if __name__ == '__main__':
    asyncio.run(main())