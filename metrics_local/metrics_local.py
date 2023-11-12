import argparse
import threading
import time
import bottle
from bottle import request, route, run, template, HTTPError
import json
import logging
import os
import sys
import stat

# Setup basic logging
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

# Set up the command line argument parser
parser = argparse.ArgumentParser(description="Start the web server with specified data directory.")

default_log_root = os.environ.get('OLA_ML_DATA_ROOT', os.path.join(os.path.dirname(__file__), "../data"))
parser.add_argument('--data-root', type=str, default=default_log_root,
                    help='The directory path for data cache (default: %(default)s)')

default_cache_size = os.environ.get('OLA_ML_DATA_CACHE_SIZE', 10)
parser.add_argument('--data-cache-size', type=int, default=default_cache_size,
                    help='Keep the data cache under this size in MB (default: %(default)s MB)')

parser.add_argument('--purge-data-cache', action='store_true', help='Purge old files from the data cache')

args = parser.parse_args()


DATA_ROOT_PATH = args.data_root
CACHE_SIZE_MB = args.data_cache_size
PATH_MAP = {"i": "countly"}
JSON_VALUES = ["events"]

app = bottle.default_app()

def process_json_values(req):
    # Process and validate JSON values in the request.
    for key in JSON_VALUES:
        value = req.params.get(key)
        if value is not None:
            try:
                req.params.replace(key, json.loads(value))
            except json.JSONDecodeError as e:
                logging.error(f"process_json_values: Error decoding JSON for key {key}: {e}")
                return False
    return True

def generate_filename(req):
    # Generate a filename for the log based on device_id and timestamp in the request
    device_id = req.params.get("device_id", default="UNKNOWN_DEVICE")
    timestamp = req.params.get("timestamp", default="UNKNOWN_TIMESTAMP")
    return "log-{device_id}-{timestamp}.json".format(
        device_id=device_id, timestamp=timestamp)

def create_log_directory(app_dir):
    # Create the directory for storing logs.
    # We stick with the app_dir/received convention for now
    log_path_initial = os.path.join(app_dir, "received")
    try:
        os.makedirs(log_path_initial, exist_ok=True)
        return log_path_initial
    except OSError as e:
        logging.error(f"create_log_directory: Error creating directory {log_path_initial}: {e}")
        return None

def write_to_log_file(log_path, output):
    # Writes a file with the contents of 'output'
    # TODO There may be a race condition with HitchHikerSource reading from
    # incomplete files - consider using temporary file paths and moving to the right place
    try:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(output)
        return True
    except IOError as e:
        logging.error(f"write_to_log_file: Error writing to file {log_path}: {e}")
        return False

def save_request(path, req):
    # Saves the incoming request from the route path to the data cache
    app_dir = PATH_MAP.get(path)
    if not app_dir:
        return False

    logging.info("save_request: new request: " + app_dir)

    if not process_json_values(req):
        return False

    filename = generate_filename(req)
    log_path_initial = create_log_directory(os.path.join(DATA_ROOT_PATH, app_dir))
    if log_path_initial is None:
        return False

    log_path = os.path.join(log_path_initial, filename)
    count = 0
    while os.path.exists(log_path):
        log_path = log_path_initial + "-" + str(count) + ".json"
        count += 1

    try:
        output = json.dumps(dict(req.params.items()))
    except TypeError as e:
        logging.error(f"Error serializing request parameters to JSON: {e}")
        return False

    return write_to_log_file(log_path, output)

def purge_cache(directory, cache_size_kb):
    cache_size = cache_size_kb * 1024 # needs to be in bytes

    # Recursively get all files in the directory and subdirectories
    files = []
    for dirpath, dirnames, filenames in os.walk(directory):
        files.extend([os.path.join(dirpath, file) for file in filenames])

    # Calculate the total size
    # TODO We should use the actual size on disk here, not the file's size
    # This is because the files are often tiny.
    total_size = sum(os.path.getsize(f) for f in files)

    # Check if total size is greater than cache_size
    if total_size > cache_size:
        logging.info(f"purge_cache: cache total size is {total_size} of {cache_size} bytes, ")
        # Sort files by last modified date
        files.sort(key=lambda x: os.path.getmtime(x))

        # Remove files until the total size is less than cache_size
        while files and total_size > cache_size:
            oldest_file = files.pop(0)
            total_size -= os.path.getsize(oldest_file)
            logging.info(f"purge_cache: Removing \"{oldest_file}\"")
            os.remove(oldest_file)

def start_purge_cache_scheduler():
    seconds = 5 * 60 # TODO Make configurable
    while True:
        purge_cache(DATA_ROOT_PATH, CACHE_SIZE_MB * 1024)
        time.sleep(seconds)

# Bottle HTTP route configs

# Serves as a health check for service - does not configure.
@app.route('/o/sdk', method='GET')
def index():
    return json.dumps({"result": "success"})

@app.route('/<path>', method='GET')
def index(path=None):
    if save_request(path, request):
        return json.dumps({"result": "success"})
    raise HTTPError(404, "Not found")

@app.route('/<path>', method='POST')
def index(path=None):
    if save_request(path, request):
        return json.dumps({"result": "success"})
    raise HTTPError(404, "Not found")

if __name__ == "__main__":
    # Do a manual purge cache purge and exit
    if (args.purge_data_cache):
        purge_cache(DATA_ROOT_PATH, CACHE_SIZE_MB * 1024)
        sys.exit()
    # Start the scheduler thread
    scheduler_thread = threading.Thread(target=start_purge_cache_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    # Start the bottle app
    app.run(host='0.0.0.0')
