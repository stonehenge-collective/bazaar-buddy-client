#!/bin/bash
# updater.sh

LOG_FILE="/tmp/bazaar_buddy_update.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting update process"
log "Download URL: $1"
log "App Path: $2"

# Wait for app to exit
log "Waiting for app to exit..."
sleep 1
log "Wait complete"

# Download the new version
log "Downloading new version..."
curl -L "$1" -o new_bazaar_buddy.zip
if [ $? -eq 0 ]; then
    log "Download successful"
else
    log "Download failed with error code $?"
    exit 1
fi

# Extract and replace
APP_PATH=$(dirname "$2")
log "Extracting to: $APP_PATH"
unzip -o new_bazaar_buddy.zip -d "$APP_PATH"
if [ $? -eq 0 ]; then
    log "Extraction successful"
else
    log "Extraction failed with error code $?"
    exit 1
fi

log "Cleaning up zip file"
rm new_bazaar_buddy.zip

# Start the new version
log "Starting new version..."
open "$APP_PATH/BazaarBuddy.app"
if [ $? -eq 0 ]; then
    log "New version started successfully"
else
    log "Failed to start new version with error code $?"
    exit 1
fi

log "Update process completed successfully"
exit 0