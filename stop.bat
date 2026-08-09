@echo off
rem ============================================================
rem  Capital Flow Intelligence Platform - STOP servers
rem  Kills backend (uvicorn) and frontend (vite) processes.
rem ============================================================
title FII-DII Platform - Stopping servers...
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop.ps1"

echo.
pause
