#!/bin/bash

# Default values for PUID and PGID
PUID=${PUID:-1000}
PGID=${PGID:-1000}

# Create the group if it doesn't exist
if ! getent group "$PGID" > /dev/null 2>&1; then
    groupadd -g "$PGID" mygroup
else
    existing_group=$(getent group "$PGID" | cut -d: -f1)
    echo "Using existing group: $existing_group"
fi

# Create the user if it doesn't exist
if ! id -u "$PUID" > /dev/null 2>&1; then
    useradd -u "$PUID" -g "$PGID" -m -s /bin/bash myuser
else
    existing_user=$(getent passwd "$PUID" | cut -d: -f1)
    echo "Using existing user: $existing_user"
fi

# Assign the user to the existing group if the group already existed
if getent passwd myuser > /dev/null 2>&1; then
    usermod -aG "$PGID" myuser
fi

# Change ownership of the home directory
chown -R "$PUID:$PGID" /home/myuser

chown -R "$PUID:$PGID" /downloads
chown -R "$PUID:$PGID" /storage_states

# Run the command as the specified user
exec gosu "$PUID:$PGID" python start.py "$@"
