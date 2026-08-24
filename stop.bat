@echo off
title CCTV IP Viewer - Server Stopping
echo.
echo ==========================================
echo  Stopping CCTV IP Viewer Server
echo ==========================================
echo.

; Kill the Python server process
echo Stopping server process...
taskkill /f /im python.exe >nul 2>&1

if %errorlevel% equ 0 (
    echo [OK] Server process stopped.
) else (
    echo [INFO] No Python process found running.
)

; Also try killing by command line
echo.
echo Attempting cleanup...
del /f /q cctv_server.log 2>nul

echo.
echo ==========================================
echo  Server stopped.
echo ==========================================
echo.
echo  To restart, run start.bat
echo.
pause