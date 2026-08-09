@echo off
rem ============================================================
rem  Capital Flow Intelligence Platform - START servers
rem  Backend  -> http://localhost:8001
rem  Frontend -> http://localhost:5173
rem  Double-click to start both. Run stop.bat to shut down.
rem ============================================================
title FII-DII Platform - Starting servers...
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1"

echo.
echo Press any key to close this window (servers keep running in background).
pause >nul
