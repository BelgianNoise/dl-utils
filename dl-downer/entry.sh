#!/usr/bin bash

PUID=${PUID:-6969}
PGID=${PGID:-6969}

groupmod -o -g "$PGID" myGroup
usermod -o -u "$PUID" myUser

chown myUser:myGroup /downloads
chown myUser:myGroup /cdm
chown myUser:myGroup /storage_states

id
