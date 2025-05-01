#!/bin/bash

here="$(dirname "$(realpath "$0" 2> /dev/null || grealpath "$0")")"
PROJECT_ROOT="$here/.."

USER_ID="$1"

while true; do
    # Run the Python command and capture its output
    OUTPUT=$(python "$PROJECT_ROOT/run_cli.py" --password=123456 deleteuser --delete-data --user-id "$USER_ID")

    # Extract the new user id from the output
    # Assumes the output line: user with id `NEWID` was created and started in it's place.
    NEW_USER_ID=$(echo "$OUTPUT" | grep -oP "user with id \`\K[^\`]+\` was created and started in it's place\." | cut -d'`' -f1)

    # If extraction failed, exit to avoid infinite loop
    if [ -z "$NEW_USER_ID" ]; then
        echo "Failed to extract new user id. Output was:"
        echo "$OUTPUT"
        exit 1
    fi

    echo "Deleted user $USER_ID, new user is $NEW_USER_ID"
    USER_ID="$NEW_USER_ID"
done