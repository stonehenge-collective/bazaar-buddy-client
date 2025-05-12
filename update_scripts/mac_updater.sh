#!/bin/bash
# updater.sh

# Wait for app to exit
echo "Waiting for app to exit..."
sleep 1

# Extract and replace
APP_PATH=$(dirname "$2")
echo "Executable path: $APP_PATH"

echo "Unzipping update from $1 to $APP_PATH"
unzip -o "$1" -d "$APP_PATH"

# Start the new version in background
nohup "$APP_PATH/BazaarBuddy.app/Contents/MacOS/BazaarBuddy" > /dev/null 2>&1 &

# Exit the updater
exit 0