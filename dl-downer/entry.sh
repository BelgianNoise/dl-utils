#!/usr/bin bash

PUID=${PUID:-6969}
PGID=${PGID:-6969}

groupmod -o -g "$PGID" myGroup
usermod -o -u "$PUID" myUser

chown -R myUser:myGroup /downloads
# chown -R myUser:myGroup /cdm
chown -R myUser:myGroup /storage_states
