import bottle
from bottle import request, route, run, template, HTTPError
import json
import logging
import os

LOG_ROOT = os.path.join(os.path.dirname(__file__), "data")
PATH_MAP = {"i": "countly"}
JSON_VALUES = ["events"]

app = bottle.default_app()

#TODO: Periodically check disk storage, rotate files to another dir, then delete
#TODO: Environment or cmdline arguments for LOG_ROOT
#TODO: gRPC endpoint to retrieve logs
#TODO: Unit tests

def save_request(path, req):
    app_dir = PATH_MAP.get(path)
    if not app_dir:
        return False
    logging.error("Saving new request: " + app_dir)
    for key in JSON_VALUES:
        value = req.params.get(key)
        if value is not None:
            try:
                # Try parsing the JSON value
                req.params.replace(key, json.loads(value))
            except json.JSONDecodeError as e:
                logging.error(f"Error decoding JSON for key {key}: {e}")
                return False

    device_id = req.params.get("device_id", default="UNKNOWN_DEVICE")
    timestamp = req.params.get("timestamp", default="UNKNOWN_TIMESTAMP")

    filename = "log-{device_id}-{timestamp}".format(
        device_id=device_id, timestamp=timestamp)

    try:
        output = json.dumps(dict(req.params.items()))
    except TypeError as e:
        logging.error(f"Error serializing request parameters to JSON: {e}")
        return False
    
    log_path_initial = os.path.join(LOG_ROOT, app_dir, "received")
    os.makedirs(log_path_initial, exist_ok=True)
    try:
        os.makedirs(log_path_initial, exist_ok=True)
    except OSError as e:
        logging.error(f"Error creating directory {log_path_initial}: {e}")
        return False

    log_path_initial = os.path.join(log_path_initial, filename)
    log_path = log_path_initial + ".json"
    count = 0
    
    while os.path.exists(log_path):
        log_path = log_path_initial + "-" + str(count) + ".json"
        count += 1

    try:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(output)
    except IOError as e:
        logging.error(f"Error writing to file {log_path}: {e}")
        return False
    
    return True

# Remote config not supported
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
