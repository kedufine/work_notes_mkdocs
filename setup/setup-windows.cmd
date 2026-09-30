@echo off
rem Double-click to install everything needed for this project (Windows).
chcp 65001 >nul
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup-windows.ps1" -Pause
