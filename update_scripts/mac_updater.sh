#!/bin/bash
# updater.sh

# Wait for app to exit
log "Waiting for app to exit..."
sleep 1

# Download the new version
curl -L "$1" -o new_bazaar_buddy.zip

# Extract and replace
APP_PATH=$(dirname "$2")
unzip -o new_bazaar_buddy.zip -d "$APP_PATH"
rm new_bazaar_buddy.zip

# Start the new version
open "$APP_PATH/BazaarBuddy.app"

# Exit the updater
exit 0