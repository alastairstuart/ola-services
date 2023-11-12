#!/bin/sh

# Check if URL is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <URL>"
    exit 1
fi

# Base URL provided as the first argument
BASE_URL=$1

# Combine seconds and milliseconds
# 'date is not used as macOS/BSD date doesn't support nanoseconds'
CURRENT_TIMESTAMP=$(python3 -c 'from time import time; print(int(round(time() * 1000)))')

# Get current hour of the day
CURRENT_HOUR=$(date +%H)

# Get current numerical day of the week (1=Monday, 7=Sunday)
CURRENT_DOW=$(date +%u)

# Path and query string
# Checksum will not be valid but sufficient for current purposes
PATH_QUERY="/i?app_key=aee33f197f73bc5f7ca99261a6f253caa2d4f614&timestamp=${CURRENT_TIMESTAMP}&hour=${CURRENT_HOUR}&dow=${CURRENT_DOW}&tz=0&sdk_version=20.04&sdk_name=java-native-android&user_details=%7B%22custom%22%3A%7B%22device_id%22%3A%22CQ8D%22%2C%22ota%22%3A%221%22%7D%7D&device_id=79b5c513422783f4&checksum=7c8e0f1ebfdd4d9164ac9f53ae2f243d9de6a9dc"

# User agent string
USER_AGENT="Dalvik/2.1.0 (Linux; U; Android 14; sdk_gphone64_arm64 Build/UE1A.230829.030)"

# Perform GET request
curl -X GET "${BASE_URL}${PATH_QUERY}" -H "User-Agent: ${USER_AGENT}"
echo