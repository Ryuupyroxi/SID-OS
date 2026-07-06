@echo off
title SID OS - Super Intelligent Distro
chcp 65001 > nul

:: SID OS Launcher for Windows
:: This is the main entry point for Windows users.
:: If Python is not found, guides user through installation.

cd /d "%~dp0"

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 goto nopython

:: Check if SID is in portable mode or dev mode
if exist "..\src\main.py" (
    cd ..
    python src\main.py %*
) else (
    python src\main.py %*
)
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Something went wrong. Try running get-sid.bat first.
    pause
)
goto end

:nopython
echo.
echo ========================================
echo  Python is not installed on this system
echo ========================================
echo.
echo Windows does not include Python by default.
echo SID OS requires Python 3.8 or later.
echo.
echo To get started quickly:
echo   1. Run: .\get-sid.bat
echo   2. It will guide you through setting up Python and SID
echo.
echo Or install Python manually:
echo   1. Download from: https://www.python.org/downloads/
echo   2. Run the installer
echo   3. IMPORTANT: Check "Add Python to PATH"
echo   4. Run this script again
echo.
echo Opening Python download page...
start https://www.python.org/downloads/
echo.
pause

:end
