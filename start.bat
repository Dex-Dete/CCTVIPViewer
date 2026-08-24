@echo off
title CCTV IP Viewer - Server Starting
echo.
echo ==========================================
echo  Starting CCTV IP Viewer Server
echo ==========================================
echo.

; Check if already running
findstr /i "CCTV IP Viewer" "%USERPROFILE%\startmenu\programs\startup\cctv.lnk" 2>nul
if %errorlevel% equ 0 (
    echo [WARNING] CCTV IP Viewer appears to already be running.
    echo.
    choice /c YN /m "Do you want to restart it?"
    if errorlevel 2 goto end
)

; Start the Python server in background
echo.
echo Starting server on port 8080...
echo.

python scripts\server.py > cctv_server.log 2>&1

set errorlevel=%errorlevel%
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to start server.
    echo Check cctv_server.log for details.
    echo.
    type cctv_server.log
    pause
    exit /b 1
)

echo [OK] Server started successfully.
echo.
echo  Access the web interface at: http://localhost:8080
echo  Access from phone/tablet: http://YOUR_PC_IP:8080
echo.
echo  Press any key to continue watching the stream setup...
echo.

pause >nul

; Create startup link for persistence
mkdir "%USERPROFILE%\startmenu\programs\startup" 2>nul
copy %~dp0cctv.vbs "%USERPROFILE%\startmenu\programs\startup\cctv.lnk" >nul 2>&1

echo.
echo ==========================================
echo  Server is running in background
echo  Press Ctrl+C in this terminal to stop
echo ==========================================
echo.

:wait
timeout /t 60 >nul
goto wait

:end