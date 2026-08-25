# Hikvision DVR Viewer

A lightweight Hikvision DVR/NVR viewer for local networks.

## Features

- **Hikvision DVR Scan**: Scans the local subnet for Hikvision DVR/NVR web interfaces
- **Manual DVR IP Entry**: Connect directly to a known DVR IP such as `192.168.1.4`
- **DVR Login**: Tries the default `admin` / `Admin@123` first, then accepts the password you enter
- **Channel Viewer**: Loads the DVR/NVR channel list and shows each camera channel through the local server
- **Multi-device Access**: Access your CCTV feeds from any device on the same network (phone, tablet, PC, iPhone)
- **Beautiful UI**: Clean, responsive interface optimized for all screen sizes
- **Continuous Streaming**: Keeps cameras alive with automatic reconnection every 3 minutes
- **Persistent Configuration**: Login details saved automatically after first setup
- **Lightweight**: Optimized for Intel Celron 2GB RAM computers

## Quick Start

1. **Run install.bat** - Will set up everything automatically
2. **Run start.bat** - Starts the local server in background
3. **Open browser** - Go to `http://localhost:8080` or use your PC's local IP address
4. **Scan network** - Click "Scan Hikvision DVRs" to detect DVR/NVR devices
5. **Connect manually if needed** - Enter the DVR IP, username, and password
6. **View feeds** - The app loads the DVR channels and refreshes each camera snapshot

## Requirements

- Windows OS
- Python 3.x (installed automatically by install.bat)
- Local network connection
- CCTV camera on the same network (RTSP/HTTP/MJPEG supported)

## How It Works

1. **DVR Discovery**: The Python server checks local IPs for Hikvision ISAPI endpoints
2. **Authentication**: The server logs in to the DVR using HTTP Basic/Digest authentication
3. **Channel Loading**: The app reads `/ISAPI/Streaming/channels` from the DVR
4. **Feed Display**: The browser loads snapshots through `/api/dvr/snapshot`, so credentials stay on the local server
3. **Keep-Alive Mechanism**: Automatically refreshes streams every 3 minutes to prevent disconnection
5. **Configuration**: Saves DVR IP and credentials to `dvr_config.csv` for future local use

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
├── scripts/server.py    # Python HTTP server and Hikvision ISAPI bridge
├── install.bat          # Installation script
├── start.bat            # Start server script
├── stop.bat             # Stop server script
├── README.md            # This file
└── AI.md               # Future AI enhancements
```

## Default Credentials

- **Username**: admin
- **Password**: Admin@123

If that password is wrong, enter the real DVR password and click Connect.

## License

This project is open source and free to use.
