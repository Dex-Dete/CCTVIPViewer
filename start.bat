@echo off
title CCTV IP Viewer - Server Start
echo.
echo ==========================================
echo  CCTV IP Viewer - Server Starting
echo ==========================================
echo.

:: Check if we're in the right directory
if not exist "index.html" (
    echo.
    echo [ERROR] index.html not found in current directory.
    echo Please run this from the CCTVIPViewer folder.
    echo.
    pause
    exit /b 1
)

echo [OK] Found index.html.

:: Check if Python is installed
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

:: Check if server.py exists
if not exist "scripts\server.py" (
    echo.
    echo [ERROR] scripts\server.py not found.
    echo Current directory: %CD%
    echo.
    pause
    exit /b 1
)

echo [OK] Found scripts\server.py.

:: Kill any existing Python processes (clean start)
echo.
echo Cleaning up any existing server processes...
taskkill /f /im python.exe 2>nul
timeout /t 1 >nul

:: Start the Python server
echo.
echo Starting CCTV IP Viewer Server on port 8080...
echo.

python scripts\server.py >"%~dp0cctv_server.log" 2>&1

set last_error=%errorlevel%
if %last_error% neq 0 (
    echo.
    echo [ERROR] Failed to start server.
    echo Check %~dp0cctv_server.log for details.
    echo.
    if exist "%~dp0cctv_server.log" type "%~dp0cctv_server.log"
    pause
    exit /b 1
)

echo [OK] Server started successfully.
echo.
echo  Web interface: http://localhost:8080
echo  Local network: http://192.168.1.7:8080 (or your PC's IP)
echo.

:: Create persistent startup link
echo.
echo Setting up persistent startup...
mkdir "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup" 2>nul
echo @echo off > "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\CCTV_Viewer.bat"
echo python "%~dp0scripts\server.py" >> "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\CCTV_Viewer.bat"

echo.
echo ==========================================
echo  Server is running in background
echo  Press Ctrl+C in this terminal to stop
echo ==========================================
echo.

:: Wait - keep the batch running but server is background
timeout -1 >nul