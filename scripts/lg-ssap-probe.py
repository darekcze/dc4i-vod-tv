#!/usr/bin/python3
"""Paired LG webOS SSAP power-state probe / explicit wake action.

Uses the user's existing LGWebOSRemote pairing configuration.
Never prints the private client key or triggers pairing on purpose.
Default --action state is read-only; --action screen-on or back changes display.
"""
import argparse
import base64
import copy
import hashlib
import json
import os
import re
import subprocess
import runpy
import socket
import ssl
import struct
import sys
import time
from pathlib import Path

ROOT = Path("/Volumes/AI-Hot/Services/LGWebOSRemote")
DEVICE = "LG_OLED55G42LW"
HOST = "192.168.1.60"

def send_wol_from_arp():
    # Use the actual LAN interface MAC rather than a potentially stale saved MAC.
    result = subprocess.run(['/usr/sbin/arp', '-n', HOST], capture_output=True, text=True, timeout=2, check=True)
    match = re.search(r'\bat\s+([0-9a-f:]+)\s+on\s+en0', result.stdout.lower())
    if not match:
        raise ValueError('TV LAN MAC unavailable from verified ARP route')
    parts = match.group(1).split(':')
    if len(parts) != 6:
        raise ValueError('invalid ARP hardware address')
    mac = bytes(int(x, 16) for x in parts)
    gateway = subprocess.run(['/usr/sbin/arp', '-n', '192.168.1.1'], capture_output=True, text=True, timeout=2)
    gateway_match = re.search(r'\bat\s+([0-9a-f:]+)\s+on\s+en0', gateway.stdout.lower())
    if gateway_match and bytes(int(x, 16) for x in gateway_match.group(1).split(':')) == mac:
        raise ValueError('ARP points to gateway instead of TV')
    packet = b'\xff' * 6 + mac * 16
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(packet, ('192.168.1.255', 9))
        s.sendto(packet, (HOST, 9))
    print('WAKE_PACKET_SENT_TO_LAN_MAC', flush=True)


class WS:
    def __init__(self, url_host=HOST, port=3001, uri="/", tls=True, seconds=3.0):
        self.raw = socket.create_connection((url_host, port), timeout=seconds)
        self.raw.settimeout(seconds)
        self.sock = ssl._create_unverified_context().wrap_socket(self.raw, server_hostname=url_host) if tls else self.raw
        self.sock.settimeout(seconds)
        self.buf = b""
        key = base64.b64encode(os.urandom(16)).decode()
        request = (
            f"GET {uri} HTTP/1.1\r\nHost: {url_host}:{port}\r\nUpgrade: websocket\r\n"
            f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        ).encode()
        self.sock.sendall(request)
        response = b""
        while b"\r\n\r\n" not in response:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("websocket HTTP handshake closed")
            response += chunk
            if len(response) > 20000:
                raise ValueError("oversized websocket HTTP handshake")
        header, self.buf = response.split(b"\r\n\r\n", 1)
        if not header.startswith(b"HTTP/1.1 101 "):
            raise ConnectionError("websocket server did not accept upgrade")
        expected = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
        if f"sec-websocket-accept: {expected}".lower() not in header.decode(errors="replace").lower():
            raise ConnectionError("invalid websocket server accept header")

    def read(self, n):
        while len(self.buf) < n:
            chunk = self.sock.recv(max(4096, n - len(self.buf)))
            if not chunk: raise ConnectionError("websocket connection closed")
            self.buf += chunk
        result, self.buf = self.buf[:n], self.buf[n:]
        return result

    def send(self, data, opcode=1):
        if isinstance(data, str): data = data.encode()
        mask = os.urandom(4)
        n = len(data)
        head = bytes([0x80 | opcode])
        if n < 126: head += bytes([0x80 | n])
        elif n < 65536: head += bytes([0xfe]) + struct.pack(">H", n)
        else: head += bytes([0xff]) + struct.pack(">Q", n)
        body = bytes(a ^ mask[i % 4] for i, a in enumerate(data))
        self.sock.sendall(head + mask + body)

    def recv(self):
        parts = []
        while True:
            x, y = self.read(2)
            opcode = x & 0x0F
            fin = bool(x & 0x80)
            size = y & 0x7F
            if size == 126: size = struct.unpack(">H", self.read(2))[0]
            if size == 127: size = struct.unpack(">Q", self.read(8))[0]
            if size > 2_000_000: raise ValueError("oversize websocket message")
            mask = self.read(4) if y & 0x80 else None
            payload = self.read(size)
            if mask: payload = bytes(c ^ mask[i % 4] for i, c in enumerate(payload))
            if opcode == 9:
                self.send(payload, opcode=10)
                continue
            if opcode == 8: raise ConnectionError("websocket closed by TV")
            if opcode in (0, 1, 2): parts.append(payload)
            if fin and opcode in (0, 1, 2):
                return b"".join(parts).decode("utf-8", errors="replace")

    def close(self):
        try: self.sock.close()
        except OSError: pass


def query(ws, request):
    ws.send(json.dumps(request, separators=(",", ":")))
    for i in range(6):
        message = json.loads(ws.recv())
        if message.get("id") == request["id"]:
            return message
        if message.get("type") == "error":
            return message
    raise TimeoutError("request response not received")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=["state", "foreground", "screen-on", "back"], default="state")
    parser.add_argument("--timeout", type=float, default=3)
    parser.add_argument("--wake-first", action="store_true")
    args = parser.parse_args()
    if args.timeout < 0.5 or args.timeout > 10: raise ValueError("invalid timeout")

    config = json.loads((ROOT / ".config/lgtv/config.json").read_text())[DEVICE]
    if not config.get("key"): raise ValueError("missing pre-paired client key")
    source = runpy.run_path(str(ROOT / "source/LGTV/payload.py"))
    hello = copy.deepcopy(source["hello_data"])
    hello["payload"]["client-key"] = config["key"]
    # Do not request new pairing on failure; use only the previously paired key.
    hello["payload"]["forcePairing"] = False
    hello["payload"]["pairingType"] = "PROMPT"
    if args.wake_first:
        send_wol_from_arp()
        time.sleep(0.6)
    ws = WS(seconds=args.timeout)
    try:
        response = query(ws, hello)
        if response.get("type") != "registered":
            print("REGISTER_FAILED", response.get("type", "unknown"), response.get("error", ""), flush=True)
            return 30
        print("PREPAIRED_REGISTERED", flush=True)
        if args.action == "state":
            response = query(ws, {"id":"dc4i-power-state-1","type":"request","uri":"ssap://com.webos.service.tvpower/power/getPowerState"})
            payload = response.get("payload", {})
            print("POWER_RESPONSE", json.dumps({k:payload.get(k) for k in ("returnValue","state","processing","errorCode","errorText") if k in payload}), flush=True)
            return 0 if payload.get("returnValue") else 31
        if args.action == "foreground":
            response = query(ws, {"id":"dc4i-foreground-1","type":"request","uri":"ssap://com.webos.applicationManager/getForegroundAppInfo"})
            payload = response.get("payload", {})
            print("FOREGROUND_RESPONSE", json.dumps({k:payload.get(k) for k in ("returnValue","appId","windowId","processId","errorCode","errorText") if k in payload}), flush=True)
            return 0 if payload.get("returnValue") else 35
        if args.action == "screen-on":
            response = query(ws, {"id":"dc4i-screen-on-1","type":"request","uri":"ssap://com.webos.service.tvpower/power/turnOnScreen","payload":{"standbyMode":"active"}})
            payload = response.get("payload", {})
            print("SCREEN_ON_RESPONSE", json.dumps({k:payload.get(k) for k in ("returnValue","errorCode","errorText") if k in payload}), flush=True)
            return 0 if payload.get("returnValue") else 32
        if args.action == "back":
            response = query(ws, {"id":"dc4i-pointer-1","type":"request","uri":"ssap://com.webos.service.networkinput/getPointerInputSocket"})
            payload = response.get("payload",{})
            socketpath = payload.get("socketPath")
            if not socketpath: print("POINTER_SOCKET_UNAVAILABLE"); return 33
            from urllib.parse import urlsplit
            uri = urlsplit(socketpath)
            if uri.scheme not in ("ws","wss") or uri.hostname != HOST:
                print("UNTRUSTED_POINTER_SOCKET");return 34
            print("POINTER_ENDPOINT", "scheme="+uri.scheme, "port="+str(uri.port), "path_length="+str(len(uri.path)), "has_query="+str(bool(uri.query)), flush=True)
            # Always Ready may restrict concurrent TLS sessions. Release SSAP control
            # after obtaining the authorized pointer socket URL, before opening pointer input.
            ws.close()
            time.sleep(0.15)
            remote = WS(url_host=HOST,port=uri.port or (3001 if uri.scheme=="wss" else 3000), uri=uri.path or "/",tls=uri.scheme=="wss",seconds=args.timeout)
            try:
                remote.send("type:button\nname:BACK\n\n")
                time.sleep(0.5)  # allow the TV input service to process the key before socket close
                print("BACK_KEY_SENT", flush=True)
            finally:
                remote.close()
            return 0
    finally:
        ws.close()
    return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, TimeoutError, ValueError, ConnectionError) as exc:
        print("SSAP_ERROR", type(exc).__name__, str(exc)[:180], flush=True)
        sys.exit(40)
