#!/bin/bash

# Check if a version number was provided
if [ -z "$1" ]; then
    echo "Error: Please provide a version number"
    echo "Usage: ./tag_version.sh X.Y.Z"
    exit 1
fi

# Create and push the tag
git tag -a "v$1" -m "Version $1"
git push origin "v$1"

echo "Version v$1 tagged and pushed successfully!"
