@echo off
setlocal
title CCTV IP Viewer - Server Stop
cd /d "%~dp0"

echo.
echo ==========================================
echo  Stopping CCTV IP Viewer Server
echo ==========================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*scripts\server.py*' -or $_.CommandLine -like '*scripts/server.py*' }; if (-not $procs) { exit 2 }; $procs | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }; exit 0"

if %errorlevel% equ 0 (
    echo [OK] CCTV server process stopped.
) else (
    echo [INFO] No CCTV server process found.
)

echo.
echo ==========================================
echo  Server stopped.
echo ==========================================
echo.
pause
