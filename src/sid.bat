@echo off
REM SID OS Launcher for Windows
REM Requires: Python 3.8+ (get it at python.org)
REM
REM Usage:
REM   sid.bat --theme vt100
REM   sid.bat --help
cd /d "%~dp0"
python src\main.py %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo If Python is not found, install it from https://python.org
    echo Make sure to check "Add Python to PATH" during installation.
    pause
)
