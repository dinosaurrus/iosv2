# Upstream HackiOS adaptation for spes — 2026-11-15

Reviewed repositories:

| repository | role |
| --- | --- |
| [JopangJovan/hackios-xnu-kernel-umi](https://github.com/JopangJovan/hackios-xnu-kernel-umi) | Xiaomi Mi 10 (`umi`, SM8250) port on top of the HackiOS kernel |
| [JopangJovan/hackios-xnu-userland-umi](https://github.com/JopangJovan/hackios-xnu-userland-umi) | that port's userland overlays |
| [oosexgang/hakios-uefi](https://github.com/oosexgang/hakios-uefi) | XNUP / Mu-Silicium UEFI boot chain and branding |
| [oosexgang/hakios-xnu-kernel](https://github.com/oosexgang/hakios-xnu-kernel) | shared HackiOS kernel drivers |
| [oosexgang/hakios-metal](https://github.com/oosexgang/hakios-metal) | native Metal driver for the Adreno (moved into the kernel repository) |

Ported to spes:

| patch | upstream | what |
| --- | --- | --- |
| `0169-spes-wifi-glink-smem-bounds.patch` | `79b00afb708a` Wi-Fi bring-up review | SMEM/GLINK/QRTR lengths chosen by the modem checked in 64 bits |
| `0170-spes-wlan-service-node.patch` | `80f5042c85b9` `hakios.wlan.cpp` | Wi-Fi controller is an `IONetworkController`/`IOEthernetController`/`IO80211Controller`; `local-mac-address` on the device-tree `wlan` node |
| `0171-spes-gpu-wait-buffer-safety.patch` | `7822f30f5016` GPU review | wait-timeout overflow, double-close of a buffer, wait on a never-issued fence |
| `0172-spes-surface-memory-bounds.patch` | `7822f30f5016` display review | plane size in 64 bits; a directly shown surface checked against its own memory |

## Wi-Fi: what HackiOS changed, and how spes differs

HackiOS's radio (POCO X5 Pro, WCN6750) is brought up from nothing: WPSS firmware,
SMEM, SMP2P, IPCC, GLINK, QRTR, WLFW, WMI and HTT. Spes already carries the same
architecture in `SpesModem.cpp` (patch 0099 onward), so the commits that matter are
the ones about values the modem chooses:

- `79b00afb708a` bounds every remote length/offset. 0169 applies the same class of
  check to spes's SMEM item walk, GLINK RX ring and QRTR headers.
- `80f5042c85b9` changes only the registry objects around the interface:
  `HakiosWLAN` becomes an `IONetworkController` under the device-tree `wlan` node
  and writes the radio address there as `local-mac-address`. MobileGestalt reads
  that property first; without it, every bundle lsd registers costs up to 5 s while
  MobileGestalt waits for an `IONetworkController` under the node. A full
  LaunchServices rebuild on an empty data volume then takes hours with SpringBoard
  waiting. Spes's ADT has the `wlan` node (`tools/mkadt.py`), but under `arm-io`,
  and the platform expert publishes nubs for the top level only, so 0170 sets the
  property on the device-tree entry itself and keeps the controller under the
  platform. On a tree whose `wlan` node is a published nub the controller goes
  under the node, as upstream does.

Not ported from the UMI repositories:

- `devices/xiaomi-mi-10/drivers/umi/hakios.umi_wifi.c` and
  `overlays/wifi/lx/*` are a QCA6390 PCIe/MHI port with a Linux-derived `lx_*`
  stack. Spes's WCN3988 is a GLINK/QRTR part handled by `SpesModem.cpp`; the two
  do not share a bus, firmware format or message layer.
- `lx_wpa.c` adds MD5 and RC4 for RSN's legacy TKIP key descriptor (WPA1). Spes's
  handshake is WPA2-PSK (HMAC-SHA1 MIC, AES key unwrap) with CCMP pairwise keys and
  optional TKIP **group** keys. A WPA1/TKIP **pairwise** path would need a second
  handshake variant and a device to validate it; adding it blind risks the working
  CCMP path. A TKIP-only access point can associate but will not pass traffic.
- UMI's battery, charger, DSI brightness, flashlight, camera and `HakiosMetal`
  overlays are SM8250/MI 10 specific.

## UEFI and Metal

- `hakios-uefi` replaces the boot chain (XNUP/Mu-Silicium UEFI, its own loader and
  branding). Spes boots through the direct shim
  (`ABL -> fastboot boot -> iosv2 shim -> XNU + ADT`). Adopting UEFI would replace
  a working chain and does not contain a driver fix that the shim path can use.
- `hakios-metal` is a native Metal driver writing PM4 packets for the Adreno 642L
  (`0x06030500`) through `HakiosGPU`. Spes's A610 (`0x06010000`) draws through
  metal2vulkan/NegroniMetal and Turnip; the Mesa `ir3-*` patches the HackiOS tree
  uses are byte-identical to the ones `tools/build-spes-turnip-macos.sh` applies at
  `b4c5513`, so there is nothing newer to take there. The portable part of the
  graphics review was the generic service code, which is 0171/0172.

Also not applicable: the recent `var-store` and `soc-args` fixes are host-side
Python tools in the upstream CI, not kernel code; spes uses `tools/adt.py` and
`tools/mkadt.py`. The latest touch and framebuffer commits are redwood register
work, not A610/SM6225.

## Testing

```
fastboot boot boot-spes-hackios.img
```

Expected new lines in the kernel log: `RedwoodWLAN: ...` once, no
`5 s` MobileGestalt stalls on first boot, and the same `SPES WIFI` / `WLAN
FIRMWARE READY` lines as before. If Wi-Fi fails, boot
`boot-spes-hackios-safe.img` (`modem=0 wifi=0`) to separate the radio path from
the rest of the system, and pull a log with `tools/sweet-log-pull.sh`.
