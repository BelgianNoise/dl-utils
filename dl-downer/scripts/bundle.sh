#!/bin/sh
BUNDLE_NAME="./dl-downer-bundle.zip"

cd "$(dirname "$0")/.."

if [ -f "$BUNDLE_NAME" ]; then
    echo "$BUNDLE_NAME already exists. Overwrite? (y/n)"
    read answer
    if [ "$answer" != "y" ]; then
        echo "Aborted."
        exit 1
    fi
    rm "$BUNDLE_NAME"
fi

zip -r "$BUNDLE_NAME" cli.py src -x "*/__pycache__/*"
echo "Created $BUNDLE_NAME"
