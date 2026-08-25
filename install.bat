@echo off
setlocal
title CCTV IP Viewer - Installation
cd /d "%~dp0"

echo.
echo ==========================================
echo  CCTV IP Viewer Installation
echo ==========================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

if not exist "index.html" (
    echo [ERROR] index.html not found.
    echo Please run this from the CCTVIPViewer folder.
    pause
    exit /b 1
)

mkdir static\css 2>nul
mkdir static\js 2>nul
mkdir scripts 2>nul

python -c "import http.server, csv, json, socket" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Required Python standard modules are unavailable.
    pause
    exit /b 1
)

if not exist dvr_config.csv (
    echo ip,port,username,password,device_name,model,serial_number,channel_count,last_connected> dvr_config.csv
    echo [OK] Created dvr_config.csv.
) else (
    echo [OK] dvr_config.csv already exists.
)

echo.
echo ==========================================
echo  Installation Complete
echo ==========================================
echo.
echo  Start the viewer with start.bat
echo  Or run: python scripts\server.py
echo.
pause
