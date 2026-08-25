@echo off
setlocal
title CCTV IP Viewer - Server Start
cd /d "%~dp0"

echo.
echo ==========================================
echo  CCTV IP Viewer - Server Starting
echo ==========================================
echo.

if not exist "index.html" (
    echo [ERROR] index.html not found.
    echo Please run this from the CCTVIPViewer folder.
    pause
    exit /b 1
)

if not exist "scripts\server.py" (
    echo [ERROR] scripts\server.py not found.
    pause
    exit /b 1
)

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo [OK] Starting server on port 8080...
start "CCTV IP Viewer Server" /min cmd /c python "%~dp0scripts\server.py" ^>"%~dp0cctv_server.log" 2^>^&1

timeout /t 2 >nul
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r = Invoke-WebRequest -UseBasicParsing http://localhost:8080/api/status -TimeoutSec 3; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }"

if %errorlevel% neq 0 (
    echo [ERROR] Server did not respond on http://localhost:8080
    if exist "%~dp0cctv_server.log" type "%~dp0cctv_server.log"
    pause
    exit /b 1
)

echo.
echo [OK] Server is running.
echo.
echo  Web interface: http://localhost:8080
echo  Use your PC local IP from another device on the same network.
echo.
echo ==========================================
echo.
pause
