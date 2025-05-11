#!/bin/bash
# updater.sh

# Wait for app to exit
echo "Waiting for app to exit..."
sleep 1

# Create temp directory in user's home
TEMP_DIR="$HOME/Library/Application Support/BazaarBuddy/temp"
mkdir -p "$TEMP_DIR"

# Download the new version to temp directory
echo "Downloading update..."
curl -L "$1" -o "$TEMP_DIR/new_bazaar_buddy.zip"

# Extract and replace
APP_PATH=$(dirname "$2")
echo "Installing update..."
unzip -o "$TEMP_DIR/new_bazaar_buddy.zip" -d "$APP_PATH"
rm "$TEMP_DIR/new_bazaar_buddy.zip"

# Start the new version in background
nohup "$APP_PATH/BazaarBuddy.app/Contents/MacOS/BazaarBuddy" > /dev/null 2>&1 &

# Exit the updater
exit 0