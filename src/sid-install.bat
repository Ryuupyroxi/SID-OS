@echo off
REM SID OS Installer for Windows
REM Note: Full system install requires Linux.
REM This runs the interactive installer for configuration.
cd /d "%~dp0"
python src\main.py --install %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo For full system installation, use a Linux system or VM.
    pause
)
