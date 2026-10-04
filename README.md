# D-Link Eagle PRO AI - hard-coded EasyMesh MQTT broker credential `admin/admin`

The D-Link Eagle PRO AI firmware (R15 1.22, E15 1.20, R32 1.10, M32 1.11) ships an EasyMesh
(Multi-AP) MQTT broker whose account credential is hard-coded in the `commander` daemon. Every
unit and every listed firmware version uses the same username and password, `admin` / `admin`, and
the owner cannot change it because it is not a user-configurable value.

`commander` writes the broker configuration at runtime:

```
/etc/emDaemon/mosquitto.conf:
  user root
  listener 1883 0.0.0.0          # R32/M32; R15/E15 emit "port 1883" (equivalent, all interfaces)
  allow_anonymous false
  password_file /etc/emDaemon/passwd

/etc/emDaemon/passwd:
  admin:admin
```

and then starts `EasyMeshDaemon`, which launches the shipped `mosquitto` broker with that
configuration. Any peer that can reach TCP/1883 (LAN, or a node bridged onto the EasyMesh
backhaul) can connect with `admin/admin` and subscribe/publish the EasyMesh control topics the
daemon itself uses (`acs/set_channel/toOne/#`, `acs/sitesurvey/toAllMembers/#`,
`acs/memberreport/toMaster/#`).

Reproduction is confirmed: with the configuration written exactly as `commander` emits it, the
shipped broker accepts `admin/admin` (MQTT CONNACK success) while `admin/wrong` is rejected as
"not authorised" and an anonymous connection is refused.

```text
TCP/1883                          : 0.0.0.0:1883 LISTEN
CONNECT username=admin pw=admin   : CONNACK 0x20 0x02 0x00 0x00  (accepted)
CONNECT username=admin pw=wrong   : CONNACK 0x20 0x02 0x00 0x05  (not authorised)
CONNECT without credentials       : not authorised
```

## Evidence

| File | Content |
| --- | --- |
| [`evidence/mosquitto-auth-reproduction.txt`](evidence/mosquitto-auth-reproduction.txt) | broker start-up and CONNACK results (`admin/admin` vs wrong password vs anonymous) |
| [`evidence/commander-static-analysis.txt`](evidence/commander-static-analysis.txt) | the `commander` functions that write the credential and the broker configuration, and the EasyMesh boot/notification call path |
| [`evidence/factory-default-mesh-enabled.txt`](evidence/factory-default-mesh-enabled.txt) | the shipped default database values that enable the Mesh role |

## PoC

| File | Purpose |
| --- | --- |
| [`poc/mqtt-fixed-cred-check.py`](poc/mqtt-fixed-cred-check.py) | send raw MQTT 3.1.1 CONNECT with `admin/admin`, a wrong password and no credentials, and print the CONNACK results |
| [`poc/grep-commander-credentials.sh`](poc/grep-commander-credentials.sh) | static check for the fixed credential and broker configuration strings inside `commander` |

## Affected products

| Model | Version | Platform | Firmware SHA-256 |
| --- | --- | --- | --- |
| R15 (AX1500 Router) | 1.22 | Realtek RTL9607 / MIPS32 BE / uClibc | `e681760565d435a0d8773a2dcf378b8cc892d6374bd83553f264094253d3c9c2` |
| E15 (AX1500 Mesh Extender) | 1.20 | Realtek RTL9607 / MIPS32 BE / uClibc | `c4f6a7ee4f1ec6bce2b2942bbd95cecfa914dd39f47ebabbc4d809469a36201d` |
| R32 (AX3200 Router) | 1.10 | MediaTek MT7622 / aarch64 / glibc | `324bf9ad9a5066eed6244bb8b97a45f4ac99835d1f11606208ed6f9092ba7790` |
| M32 (AX3200 Mesh System) | 1.11 | MediaTek MT7622 / aarch64 / glibc | `a3927fd82a8f985ad753a32b19ee944b28bd6e99761f28e71fcf7410daabe242` |

`commander` SHA-256: R15 `a6cb21192180c9227c9fa0e9978adc8c00d6a2ead9d43f39a6a1eef77f83a620`;
E15 `fe0d0a00c1cf9630921dd8419b2e4b02450aebb967520952b943fcaa65dccd56`;
R32 `2305438c6f225deb1e5fa0a75f5cb267ff84cf2b59485d74478b6ab125be6ca7`;
M32 `93533d314a1e609a01b5a62dbb6528b0c7361fe9124b411b66ae4f836ffe5b16`.

## Classification

- CWE-798: Use of Hard-coded Credentials (primary)
- CWE-1188: Insecure Default Initialization of Resource
- CWE-306: Missing Authentication for Critical Function

CVSS v3.1: `CVSS:3.1/AV:A/AC:L/PR:N/UI:N/S:U/C:L/I:H/A:L`

## Coordination

D-Link was contacted before this publication. No CVE had been assigned when this package was
prepared.
