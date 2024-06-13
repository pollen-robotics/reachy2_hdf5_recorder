#!/bin/bash

# Check if a directory is provided as an argument
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 /path/to/the/directory"
    exit 1
fi

# Path of the starting directory for the search, taken from the first script argument
SEARCH_DIR="$1"

# Name of the file to search for
FILE_NAME="gst-plugins-rs.wrap"

# Function to search and replace in the file
search_and_replace() {
    local file_path="$1"
    sed -i 's/revision=gstreamer-1.22.8/revision=0.11.3+fixup/' "$file_path"
    echo "Modification made in: $file_path"
}

# Export the function to use it with find -exec
export -f search_and_replace

# Search for the file and apply the modification
find "$SEARCH_DIR" -type f -name "$FILE_NAME" -exec bash -c 'search_and_replace "$0"' {} \;

echo "Search and modification completed."

