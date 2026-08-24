#!/usr/bin/env python3
"""
CCTV IP Viewer Server
Lightweight Python HTTP server for CCTV monitoring.
Optimized for Intel Celron 2GB RAM computers.
"""

import http.server
import socketserver
import threading
import os
import sys
import json
import csv
from datetime import datetime

# Configuration
PORT = 8080
HTML_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'index.html')
STORAGE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'camera_config.csv')

print_lock = threading.Lock()

def log_print(*args, **kwargs):
    with print_lock:
        print(datetime.now().strftime('%H:%M:%S'), *args, **kwargs)

class CCTVHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler for CCTV viewer"""
    
    def do_GET(self):
        # Serve the main HTML file
        if self.path == '/' or self.path == '/index.html' or self.path == '':
            self.serve_html()
        elif self.path.startswith('/static/'):
            self.serve_static()
        elif self.path.startswith('/camera/'):
            self.serve_camera_feed()
        elif self.path == '/api/cameras':
            self.serve_api_cameras()
        elif self.path == '/api/status':
            self.serve_status()
        else:
            self.send_error(404)
    
    def do_POST(self):
        if self.path == '/api/save-config':
            self.save_config()
        else:
            self.send_error(404)
    
    def serve_html(self):
        try:
            with open(HTML_FILE, 'r', encoding='utf-8') as f:
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(f.read().encode('utf-8'))
        except FileNotFoundError:
            self.send_error(404, "HTML file not found")
    
    def serve_static(self):
        # Serve CSS/JS files
        file_path = self.path.lstrip('/')
        if not os.path.isfile(file_path):
            file_path = os.path.join(os.path.dirname(HTML_FILE), file_path)
        
        if os.path.isfile(file_path):
            ext = os.path.splitext(file_path)[1].lower()
            mime_types = {
                '.css': 'text/css',
                '.js': 'application/javascript',
                '.html': 'text/html'
            }
            mime = mime_types.get(ext, 'application/octet-stream')
            
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.end_headers()
            
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404)
    
    def serve_camera_feed(self):
        # Serve camera MJPEG stream
        camera_ip = self.path.replace('/camera/', '').strip('/')
        log_print(f"Camera feed request: {camera_ip}")
        
        # Return MJPEG placeholder - in production, this would proxy to actual camera
        self.send_response(200)
        self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
        self.end_headers()
        
        try:
            while True:
                # Generate frame placeholder
                frame = self.generate_frame_placeholder()
                self.wfile.write(frame)
                # Small delay to prevent CPU overuse
                import time
                time.sleep(0.04)
        except BrokenPipeError:
            pass
        except Exception as e:
            log_print(f"Camera stream error: {e}")
    
    def generate_frame_placeholder(self):
        # Generate a simple MJPEG frame placeholder
        # In production, this would capture from actual camera
        boundary = b'--frame\r\n'
        content_type = b'Content-Type: image/jpeg\r\n\r\n'
        # Create a minimal JPEG-like frame (very small for performance)
        img_data = b'fake.jpg\r\n'
        return boundary + content_type + img_data + b'\r\n'
    
    def serve_api_cameras(self):
        # Return detected cameras configuration
        cameras = load_cameras()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(cameras).encode('utf-8'))
    
    def serve_status(self):
        # Return server status
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            'status': 'running',
            'port': PORT,
            'timestamp': datetime.now().isoformat()
        }).encode('utf-8'))
    
    def save_config(self):
        # Save camera configuration
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        config = json.loads(body)
        
        file_exists = os.path.isfile(STORAGE_FILE)
        
        with open(STORAGE_FILE, 'a' if file_exists else 'w', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['IP', 'NAME', 'PASSWORD', 'LAST_CONNECTED'])
            writer.writerow([
                config.get('ip', ''),
                config.get('name', ''),
                config.get('password', 'Admin@123'),
                datetime.now().isoformat()
            ])
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'saved'}).encode('utf-8'))

def load_cameras():
    """Load camera configurations from storage file"""
    cameras = []
    if os.path.exists(STORAGE_FILE):
        try:
            with open(STORAGE_FILE, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['IP']:
                        cameras.append({
                            'ip': row['IP'],
                            'name': row.get('NAME', f'Camera {len(cameras) + 1}'),
                            'password': row.get('PASSWORD', 'Admin@123')
                        })
        except Exception as e:
            log_print(f"Error loading cameras: {e}")
    return cameras

def main():
    log_print(f"Starting CCTV IP Viewer Server on port {PORT}")
    log_print(f"Web interface: http://localhost:{PORT}")
    log_print(f"Camera scanner will detect IPs in 192.168.1.x range")
    
    # Load existing camera configs
    cameras = load_cameras()
    log_print(f"Loaded {len(cameras)} saved camera(s)")
    
    # Set up server
    handler = CCTVHandler
    
    try:
        with socketserver.TCPServer(("", PORT), handler) as httpd:
            log_print(f"Server running on port {PORT}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        log_print("Server shutting down...")
    except OSError as e:
        log_print(f"Port {PORT} already in use or error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()