# CCTV IP Viewer

A lightweight, easy-to-use CCTV monitoring application that works on local networks.

## Features

- **Network Scanning**: Automatically scans your local network (192.168.1.1-255) to detect CCTV cameras
- **Multi-device Access**: Access your CCTV feeds from any device on the same network (phone, tablet, PC, iPhone)
- **Beautiful UI**: Clean, responsive interface optimized for all screen sizes
- **Continuous Streaming**: Keeps cameras alive with automatic reconnection every 3 minutes
- **Persistent Configuration**: Login details saved automatically after first setup
- **Lightweight**: Optimized for Intel Celron 2GB RAM computers

## Quick Start

1. **Run install.bat** - Will set up everything automatically
2. **Run start.bat** - Starts the local server in background
3. **Open browser** - Go to `http://localhost:8080` or use your PC's local IP address
4. **Scan network** - Click "Scan Network" to detect cameras
5. **View feeds** - All detected cameras will start streaming automatically

## Requirements

- Windows OS
- Python 3.x (installed automatically by install.bat)
- Local network connection
- CCTV camera on the same network (RTSP/HTTP/MJPEG supported)

## How It Works

1. **Network Scanning**: The app pings IP addresses in your local range and checks for common camera ports (80, 8080, 554)
2. **Stream Delivery**: Uses MJPEG streaming via HTML5 video elements
3. **Keep-Alive Mechanism**: Automatically refreshes streams every 3 minutes to prevent disconnection
4. **Configuration**: Saves camera IPs and credentials to `camera_config.csv` for future use

## Optimization for Low-RAM Systems

- Uses vanilla JavaScript - no heavy frameworks (React/Vue/Angular)
- Minimal CSS - no external dependencies
- Python built-in http.server - no extra server software needed
- MJPEG streaming at efficient quality levels
- Stream refresh interval optimized to balance between keeping alive and CPU usage

## Port Forwarding (for external access)

To access from outside your local network:
1. Find your public IP: visit `whatismyip.com`
2. Log into your router
3. Set up port forwarding: External Port 8080 -> Internal IP:8080
4. Use your public IP to access the stream

## File Structure

```
CCTVIPViewer/
├── index.html          # Main web interface
├── static/css/styles.css  # Styling
├── static/js/app.js     # Application logic
├── scripts/server.py    # Python HTTP server
├── install.bat          # Installation script
├── start.bat            # Start server script
├── stop.bat             # Stop server script
├── README.md            # This file
└── AI.md               # Future AI enhancements
```

## Default Credentials

- **Username**: admin
- **Password**: Admin@123

These are saved permanently after first configuration.

## License

This project is open source and free to use.