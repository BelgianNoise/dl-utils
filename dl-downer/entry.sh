#!/bin/bash

# Default values for PUID and PGID
PUID=${PUID:-1000}
PGID=${PGID:-1000}

# Check if group already exists
if ! getent group mygroup > /dev/null 2>&1; then
  groupadd -g "$PGID" mygroup
fi

# Check if user already exists
if ! id -u myuser > /dev/null 2>&1; then
  useradd -u "$PUID" -g "$PGID" -m -s /bin/bash myuser
fi

# Change ownership of the home directory
chown -R myuser:mygroup /home/myuser

chown -R myuser:mygroup /downloads
chown -R myuser:mygroup /storage_states

# Run the command as the specified user
exec gosu myuser "$@"
