#!/bin/bash

# Check if URL is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <URL>"
    exit 1
fi

# Base URL provided as the first argument
BASE_URL=$1

# Path and query string
PATH_QUERY="/i?app_key=aee33f197f73bc5f7ca99261a6f253caa2d4f614&timestamp=1699696583746&hour=9&dow=6&tz=0&sdk_version=20.04&sdk_name=java-native-android&user_details=%7B%22custom%22%3A%7B%22device_id%22%3A%22CQ8D%22%2C%22ota%22%3A%221%22%7D%7D&device_id=79b5c513422783f4&checksum=7c8e0f1ebfdd4d9164ac9f53ae2f243d9de6a9dc"

# User agent string
USER_AGENT="Dalvik/2.1.0 (Linux; U; Android 14; sdk_gphone64_arm64 Build/UE1A.230829.030)"

# Perform GET request
curl -X GET "${BASE_URL}${PATH_QUERY}" -H "User-Agent: ${USER_AGENT}"