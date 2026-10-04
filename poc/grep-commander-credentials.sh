#!/bin/sh
# Static check: the fixed credential and broker configuration that commander writes into the
# EasyMesh MQTT broker under /etc/emDaemon/.
#
# Usage: ./grep-commander-credentials.sh /path/to/extracted/rootfs

ROOTFS="${1:-.}"

for bin in usr/bin/commander usr/sbin/commander; do
    [ -f "$ROOTFS/$bin" ] || continue
    echo "== $bin =="
    strings -n 5 "$ROOTFS/$bin" | grep -E \
        'admin:admin|allow_anonymous false|password_file /etc/emDaemon/passwd|listener 1883 0\.0\.0\.0|port 1883|user-password: admin' \
        | sort -u
done
