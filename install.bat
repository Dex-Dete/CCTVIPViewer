@echo off
title CCTV IP Viewer - Installation
echo.
echo ==========================================
echo  CCTV IP Viewer Installation
echo ==========================================
echo.

; Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python from https://python.org
    echo.
    pause
    exit /b 1
)

echo [OK] Python is installed.

; Check if we're in the right directory
if not exist "index.html" (
    echo.
    echo [ERROR] index.html not found in current directory.
    echo Please run this from the CCTVIPViewer folder.
    echo.
    pause
    exit /b 1
)

echo [OK] Found index.html.

; Create necessary directories
echo.
echo Creating directories...
mkdir static\css 2>nul
mkdir static\js 2>nul
mkdir scripts 2>nul

echo [OK] Directories ready.

; Check and install dependencies
echo.
echo Checking Python dependencies...
python -c "import http.server; import csv; import json" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Required Python modules are available.
) else (
    echo.
    echo [INFO] Installing required Python modules...
    pip install http.server retry >nul 2>&1 || echo [WARN] Some modules may need manual installation.
)

; Create camera_config.csv if it doesn't exist
if not exist camera_config.csv (
    echo.
    echo Creating camera configuration file...
    echo IP,NAME,PASSWORD,LAST_CONNECTED > camera_config.csv
    echo [OK] camera_config.csv created with default settings.
) else (
    echo [OK] camera_config.csv already exists.
)

; Create the startup shortcut
echo.
echo Creating startup batch file...
copy /y nul %~dp0start.bat >nul 2>&1

echo.
echo ==========================================
echo  Installation Complete!
echo ==========================================
echo.
echo  To start the CCTV viewer:
echo   - Double-click start.bat
echo   - OR run: python scripts\server.py
echo.
echo  To stop the server:
echo   - Double-click stop.bat
echo.
echo  Default login credentials (if prompted):
echo   Username: admin
echo   Password: Admin@123
echo.
pause