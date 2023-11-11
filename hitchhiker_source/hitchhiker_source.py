import argparse
from grpclib.server import Server
from grpclib.const import Status
from grpclib.exceptions import GRPCError
from google.protobuf.empty_pb2 import Empty
import asyncio
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

class HitchhikerSource(hitchhiker_grpc.HitchhikerSourceBase):

    async def GetSourceId(self, stream):
        logging.info(f"GetSourceId: Requested")
        await stream.send_message(hitchhiker_pb2.SourceId(id=SOURCE_ID))

    async def GetDownloads(self, stream):
        request = await stream.recv_message()
        base_directory = METRICS_PATH

        logging.info(f"GetDownloads: Requested for destination \"{request.destinationId}\" by client \"{request.clientId}\"")

        try:
            # Function to list and get file info
            def list_received_files(metrics_path):
                received_files = [os.path.join(metrics_path, file) for file in os.listdir(metrics_path) if os.path.isfile(os.path.join(metrics_path, file))]
                return received_files

            def file_info(filepath):
                filename = os.path.basename(filepath)
                with open(filepath, 'rb') as file:
                    content = file.read()
                    fileid = hashlib.md5(content).hexdigest()
                    return hitchhiker_pb2.File(fileid=fileid, filename=filename, type="application/json")

            files = [file_info(filepath) for filepath in list_received_files(base_directory)]

            # Send the list of files
            await stream.send_message(hitchhiker_pb2.FileList(files=files))

        except FileNotFoundError:
            logging.error(f"GetDownloads: Directory not found: {METRICS_PATH}")
            # Optionally, send an error message to the client or an empty list
            raise GRPCError(Status.NOT_FOUND, f"Downloads not found")

        except PermissionError:
            logging.error("GetDownloads: Permission denied.")
            raise GRPCError(Status.PERMISSION_DENIED, "Permission denied.")

        except Exception as e:
            logging.error(f"GetDownloads: Unexpected error: {str(e)}")
            raise GRPCError(Status.INTERNAL, f"Unexpected error")

    async def DownloadFile(self, stream):
        request = await stream.recv_message()
        base_directory = METRICS_PATH

        for file_info in request.files:
            try:
                filepath = os.path.join(base_directory, file_info.filename)
                
                logging.info(f"DownloadFile: Requested: \"{file_info.filename}\" by client \"{request.clientId}\"")
                
                with open(filepath, 'rb') as file:
                    content = file.read()
                    fileid = hashlib.md5(content).hexdigest()

                    await stream.send_message(hitchhiker_pb2.File(
                        fileid=fileid,
                        filename=file_info.filename,
                        type="application/json",
                        blob=content
                    ))
            except FileNotFoundError:
                logging.warning(f"DownloadFile: File not found")
                raise GRPCError(Status.NOT_FOUND, f"File not found")
            except Exception as e:
                # For other exceptions, abort and send an error message
                logging.error(f"DownloadFile: Unexpected Error: {str(e)}")
                raise GRPCError(Status.INTERNAL, f"Unexpected error")

    async def MarkDelivered(self, stream):
        request = await stream.recv_message()
        base_directory = METRICS_PATH

        for file_info in request.files:
            filepath = os.path.join(base_directory, file_info.filename)
            
            logging.info(f"MarkDelivered: Requested: \"{file_info.filename}\" to destination \"{request.destinationId}\" by client \"{request.clientId}\"")

            # Delete the file
            try:
                os.remove(filepath)
                logging.info(f"MarkDelivered: File deleted: \"{file_info.filename}\"")
            except FileNotFoundError:
                logging.warning(f"MarkDelivered: File to delete not found: \"{filepath}\"")
            except Exception as e:
                logging.error(f"MarkDelivered: Error deleting file \"{file_info.filename}\": {str(e)}")

        # Acknowledge the delivery
        await stream.send_message(Empty())

async def main():
    server = Server([HitchhikerSource()])
    await server.start('127.0.0.1', 50051)
    logging.info("HitchhikerSource service running...")
    await server.wait_closed()

if __name__ == '__main__':
    asyncio.run(main())