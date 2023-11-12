import argparse
import bottle
from bottle import request, route, run, template, HTTPError
import json
import logging
import os

# Setup basic logging
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

# Set up the command line argument parser
parser = argparse.ArgumentParser(description="Start the web server with specified data directory.")
default_log_root = os.environ.get('OLA_ML_DATA_ROOT', os.path.join(os.path.dirname(__file__), "../data"))

parser.add_argument('--data-root', type=str, default=default_log_root,
                    help='The directory path for log root (default: %(default)s)')
args = parser.parse_args()


DATA_ROOT_PATH = args.data_root
PATH_MAP = {"i": "countly"}
JSON_VALUES = ["events"]

app = bottle.default_app()

#TODO: Periodically check disk storage, rotate files to another dir, then delete

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
    app.run()
