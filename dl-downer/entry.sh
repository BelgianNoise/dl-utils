#!/bin/bash

PUID=${PUID:-6969}
PGID=${PGID:-6969}

groupadd -g "$PGID" myGroup
useradd -u "$PUID" -g myGroup myUser

chown -R myUser:myGroup /downloads
chown -R myUser:myGroup /storage_states

exec gosu myUser python start.py
