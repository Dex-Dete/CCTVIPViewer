#!/usr/bin/env python3
"""
CCTV IP Viewer Server
Finds Hikvision DVR/NVR devices, authenticates with ISAPI, and proxies channel
snapshots so the browser does not need to know the DVR password.
"""

import csv
import ipaddress
import json
import mimetypes
import os
import socket
import sys
import threading
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from socketserver import ThreadingTCPServer
from urllib.parse import parse_qs, urlparse

PORT = 8080
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML_FILE = os.path.join(ROOT_DIR, "index.html")
STORAGE_FILE = os.path.join(ROOT_DIR, "dvr_config.csv")
HTTP_PORTS = (80, 8080, 8000)
DEFAULT_CREDENTIALS = (
    ("admin", "Admin@123"),
    ("admin", "12345"),
    ("admin", "admin"),
)
SOCKET_TIMEOUT = 0.35
HTTP_TIMEOUT = 4

print_lock = threading.Lock()


def log_print(*args):
    with print_lock:
        print(datetime.now().strftime("%H:%M:%S"), *args, flush=True)


class CCTVHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("", "/", "/index.html"):
            self.serve_file(HTML_FILE, "text/html; charset=utf-8")
        elif path.startswith("/static/"):
            self.serve_static(path)
        elif path == "/api/status":
            self.send_json({"status": "running", "port": PORT, "timestamp": datetime.now().isoformat()})
        elif path == "/api/dvrs":
            self.send_json([without_password(dvr) for dvr in load_dvrs()])
        elif path == "/api/scan":
            self.scan_hikvision(parsed.query)
        elif path == "/api/dvr/snapshot":
            self.serve_snapshot(parsed.query)
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self):
        if self.path == "/api/dvr/connect":
            self.connect_dvr()
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def serve_static(self, request_path):
        relative_path = request_path.lstrip("/").replace("/", os.sep)
        file_path = os.path.abspath(os.path.join(ROOT_DIR, relative_path))
        if not file_path.startswith(ROOT_DIR) or not os.path.isfile(file_path):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        self.serve_file(file_path, content_type)

    def serve_file(self, file_path, content_type):
        try:
            with open(file_path, "rb") as handle:
                content = handle.read()
        except FileNotFoundError:
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def scan_hikvision(self, query_string):
        query = parse_qs(query_string)
        local_ip = get_local_ip()
        subnet = query.get("subnet", [local_ip.rsplit(".", 1)[0]])[0]
        start = clamp_int(query.get("start", ["1"])[0], 1, 254)
        end = clamp_int(query.get("end", ["254"])[0], start, 254)

        if not is_valid_subnet(subnet):
            self.send_error(HTTPStatus.BAD_REQUEST, "Invalid subnet")
            return

        log_print(f"Scanning for Hikvision DVR/NVR at {subnet}.{start}-{end}")
        self.send_json(scan_subnet_for_hikvision(subnet, start, end))

    def connect_dvr(self):
        try:
            payload = self.read_json_body()
        except ValueError:
            self.send_error(HTTPStatus.BAD_REQUEST, "Invalid JSON")
            return

        ip = (payload.get("ip") or "").strip()
        port = int(payload.get("port") or 80)
        username = (payload.get("username") or "admin").strip()
        password = payload.get("password") or ""

        if not is_valid_ip(ip):
            self.send_error(HTTPStatus.BAD_REQUEST, "Invalid DVR IP")
            return

        credentials = [(username, password)] if password else []
        credentials.extend(pair for pair in DEFAULT_CREDENTIALS if pair not in credentials)

        last_error = "Could not authenticate to DVR"
        for user, secret in credentials:
            result = connect_to_hikvision(ip, port, user, secret)
            if result["ok"]:
                dvr = {
                    "ip": ip,
                    "port": str(port),
                    "username": user,
                    "password": secret,
                    "device_name": result["device_name"],
                    "model": result["model"],
                    "serial_number": result["serial_number"],
                    "channel_count": str(len(result["channels"])),
                    "last_connected": datetime.now().isoformat(timespec="seconds"),
                }
                save_dvr(dvr)
                self.send_json({"dvr": without_password(dvr), "channels": result["channels"]})
                return
            last_error = result["error"]

        self.send_json({"error": last_error}, status=HTTPStatus.UNAUTHORIZED)

    def serve_snapshot(self, query_string):
        query = parse_qs(query_string)
        ip = (query.get("ip", [""])[0]).strip()
        channel = (query.get("channel", [""])[0]).strip()
        dvr = find_saved_dvr(ip)

        if not dvr or not channel:
            self.send_error(HTTPStatus.BAD_REQUEST, "Saved DVR and channel are required")
            return

        image = get_channel_snapshot(dvr, channel)
        if not image["ok"]:
            self.send_error(HTTPStatus.BAD_GATEWAY, image["error"])
            return

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", image["content_type"])
        self.send_header("Content-Length", str(len(image["data"])))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(image["data"])

    def read_json_body(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, json.JSONDecodeError) as exc:
            raise ValueError("Invalid JSON") from exc

    def send_json(self, payload, status=HTTPStatus.OK):
        content = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format_string, *args):
        log_print(f"{self.address_string()} - {format_string % args}")


def scan_subnet_for_hikvision(subnet, start, end):
    addresses = [f"{subnet}.{number}" for number in range(start, end + 1)]
    found = []
    with ThreadPoolExecutor(max_workers=48) as executor:
        futures = {executor.submit(scan_host_for_hikvision, ip): ip for ip in addresses}
        for future in as_completed(futures):
            result = future.result()
            if result:
                found.append(result)
    found.sort(key=lambda item: tuple(int(part) for part in item["ip"].split(".")))
    return found


def scan_host_for_hikvision(ip):
    for port in HTTP_PORTS:
        if not can_connect(ip, port):
            continue
        probe = unauthenticated_probe(ip, port)
        if probe["hikvision"]:
            return {
                "ip": ip,
                "port": str(port),
                "device_name": probe["device_name"],
                "model": probe["model"],
                "auth_required": probe["auth_required"],
            }
    return None


def unauthenticated_probe(ip, port):
    result = {"hikvision": False, "auth_required": False, "device_name": "", "model": ""}
    for path in ("/ISAPI/System/deviceInfo", "/doc/page/login.asp"):
        response = http_get_raw(f"http://{ip}:{port}{path}", timeout=2)
        text = response["data"][:600].decode("utf-8", errors="ignore").lower()
        headers = "\n".join(f"{key}: {value}" for key, value in response["headers"].items()).lower()
        haystack = text + "\n" + headers

        if response["status"] == 401 and path.startswith("/ISAPI/"):
            result["hikvision"] = True
            result["auth_required"] = True
        if "hikvision" in haystack or "isapi" in haystack:
            result["hikvision"] = True
        if response["status"] == 200 and "<deviceinfo" in text:
            info = parse_device_info(response["data"])
            result.update({"hikvision": True, "device_name": info["device_name"], "model": info["model"]})
        if result["hikvision"]:
            return result
    return result


def connect_to_hikvision(ip, port, username, password):
    base = f"http://{ip}:{port}"
    response = authenticated_get(base, "/ISAPI/System/deviceInfo", username, password)
    if response["status"] == 401:
        return {"ok": False, "error": "Wrong username or password"}
    if response["status"] <= 0:
        return {"ok": False, "error": response["error"]}
    if response["status"] >= 400:
        return {"ok": False, "error": f"DVR returned HTTP {response['status']}"}

    device = parse_device_info(response["data"])
    channels = load_hikvision_channels(base, username, password)
    if not channels:
        channels = fallback_channels(16)

    return {
        "ok": True,
        "device_name": device["device_name"] or f"Hikvision DVR {ip}",
        "model": device["model"],
        "serial_number": device["serial_number"],
        "channels": channels,
    }


def load_hikvision_channels(base, username, password):
    response = authenticated_get(base, "/ISAPI/Streaming/channels", username, password)
    if response["status"] >= 400 or not response["data"]:
        return []

    try:
        root = ET.fromstring(response["data"])
    except ET.ParseError:
        return []

    channels = []
    for node in root.iter():
        if strip_ns(node.tag) != "StreamingChannel":
            continue
        channel_id = child_text(node, "id")
        if not channel_id or not channel_id.endswith("01"):
            continue
        channels.append({
            "id": channel_id,
            "name": child_text(node, "channelName") or f"Camera {len(channels) + 1}",
            "enabled": child_text(node, "enabled") or "true",
            "snapshot_url": f"/api/dvr/snapshot?ip={base.split('//', 1)[1].split(':', 1)[0]}&channel={channel_id}",
        })
    return channels


def fallback_channels(count):
    return [{
        "id": f"{number}01",
        "name": f"Camera {number}",
        "enabled": "unknown",
        "snapshot_url": "",
    } for number in range(1, count + 1)]


def get_channel_snapshot(dvr, channel_id):
    base = f"http://{dvr['ip']}:{dvr.get('port', '80')}"
    paths = (
        f"/ISAPI/Streaming/channels/{channel_id}/picture",
        f"/Streaming/Channels/{channel_id}/picture",
    )
    for path in paths:
        response = authenticated_get(base, path, dvr["username"], dvr["password"])
        content_type = response["headers"].get("Content-Type", "image/jpeg")
        if response["status"] == 200 and response["data"] and "image" in content_type.lower():
            return {"ok": True, "data": response["data"], "content_type": content_type}
    return {"ok": False, "error": "Snapshot unavailable for this channel"}


def authenticated_get(base_url, path, username, password):
    password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, base_url, username, password)
    opener = urllib.request.build_opener(
        urllib.request.HTTPDigestAuthHandler(password_mgr),
        urllib.request.HTTPBasicAuthHandler(password_mgr),
    )
    request = urllib.request.Request(base_url + path, headers={"User-Agent": "CCTV-IP-Viewer/1.0"})
    try:
        with opener.open(request, timeout=HTTP_TIMEOUT) as response:
            return {
                "status": response.getcode(),
                "headers": dict(response.headers),
                "data": response.read(),
                "error": "",
            }
    except urllib.error.HTTPError as exc:
        return {"status": exc.code, "headers": dict(exc.headers), "data": exc.read(), "error": str(exc)}
    except Exception as exc:
        return {"status": 0, "headers": {}, "data": b"", "error": str(exc)}


def http_get_raw(url, timeout):
    request = urllib.request.Request(url, headers={"User-Agent": "CCTV-IP-Viewer/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return {"status": response.getcode(), "headers": dict(response.headers), "data": response.read(4096)}
    except urllib.error.HTTPError as exc:
        return {"status": exc.code, "headers": dict(exc.headers), "data": exc.read(4096)}
    except Exception:
        return {"status": 0, "headers": {}, "data": b""}


def can_connect(ip, port):
    try:
        with socket.create_connection((ip, port), timeout=SOCKET_TIMEOUT):
            return True
    except OSError:
        return False


def parse_device_info(data):
    info = {"device_name": "", "model": "", "serial_number": ""}
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return info
    info["device_name"] = child_text(root, "deviceName")
    info["model"] = child_text(root, "model")
    info["serial_number"] = child_text(root, "serialNumber")
    return info


def child_text(node, wanted_name):
    for child in node.iter():
        if strip_ns(child.tag) == wanted_name and child.text:
            return child.text.strip()
    return ""


def strip_ns(tag):
    return tag.rsplit("}", 1)[-1]


def load_dvrs():
    if not os.path.exists(STORAGE_FILE):
        return []
    dvrs = []
    try:
        with open(STORAGE_FILE, "r", newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if is_valid_ip(row.get("ip", "")):
                    dvrs.append(row)
    except Exception as exc:
        log_print(f"Could not load DVR config: {exc}")
    return dvrs


def save_dvr(dvr):
    existing = {f"{item['ip']}:{item.get('port', '80')}": item for item in load_dvrs()}
    existing[f"{dvr['ip']}:{dvr.get('port', '80')}"] = dvr
    fieldnames = ["ip", "port", "username", "password", "device_name", "model", "serial_number", "channel_count", "last_connected"]
    with open(STORAGE_FILE, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in existing.values():
            writer.writerow({field: item.get(field, "") for field in fieldnames})


def find_saved_dvr(ip):
    for dvr in load_dvrs():
        if dvr.get("ip") == ip:
            return dvr
    return None


def without_password(dvr):
    public = dict(dvr)
    public.pop("password", None)
    return public


def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "192.168.1.1"


def is_valid_ip(value):
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def is_valid_subnet(value):
    parts = value.split(".")
    if len(parts) != 3:
        return False
    return all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)


def clamp_int(value, minimum, maximum):
    try:
        number = int(value)
    except ValueError:
        number = minimum
    return max(minimum, min(number, maximum))


def main():
    log_print(f"Starting CCTV IP Viewer Server on port {PORT}")
    log_print(f"Web interface: http://localhost:{PORT}")
    log_print(f"Detected local IP: {get_local_ip()}")

    ThreadingTCPServer.allow_reuse_address = True
    try:
        with ThreadingTCPServer(("", PORT), CCTVHandler) as httpd:
            log_print(f"Server running on port {PORT}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        log_print("Server shutting down...")
    except OSError as exc:
        log_print(f"Port {PORT} already in use or error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
