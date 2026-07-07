@echo off
title SID OS Bootstrap - Windows
chcp 65001 > nul

:: SID OS - Windows Bootstrap Launcher
:: Works on Windows 7+ with or without Python
:: 
:: Double-click this file to download and run SID OS
:: If Python is not installed, it will guide you

goto menu

:menu
cls
echo.
echo =========================================================
echo    ███████╗██╗██████╗      ██████╗ ███████╗
echo    ██╔════╝██║██╔══██╗    ██╔═══██╗██╔════╝
echo    ███████╗██║██║  ██║    ██║   ██║███████╗
echo    ╚════██║██║██║  ██║    ██║   ██║╚════██║
echo    ███████║██║██████╔╝    ╚██████╔╝███████║
echo    ╚══════╝╚═╝╚═════╝      ╚═════╝ ╚═════╝
echo    SUPER INTELLIGENT DISTRO    v1.2.0
echo =========================================================
echo.
echo  SID OS - Super Intelligent Distro for Old Hardware
echo.
echo  [1] Quick Setup (download + install deps + launch)
echo  [2] Launch SID (if already downloaded)
echo  [3] Update to latest version
echo  [4] What is SID OS?
echo  [5] Exit
echo.

set /p choice="Select option [1-5]: "

if "%choice%"=="1" goto setup
if "%choice%"=="2" goto launch
if "%choice%"=="3" goto update
if "%choice%"=="4" goto about
if "%choice%"=="5" goto end
echo Invalid option. Please try again.
timeout /t 2 > nul
goto menu

:setup
echo.
echo  Setting up SID OS...
echo  Checking for Python...
python --version >nul 2>&1
if errorlevel 1 goto nopython
echo  Python found! Proceeding with setup...
cd /d "%~dp0"
if not exist "%~dp0get-sid.py" (
    echo  Downloading bootstrap script...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/Ryuupyroxi/SID-OS/main/get-sid.py' -OutFile 'get-sid.py'}"
)
python get-sid.py --setup
goto end

:launch
echo.
echo  Launching SID OS...
python --version >nul 2>&1
if errorlevel 1 goto nopython
cd /d "%~dp0"
if exist "%~dp0src\main.py" (
    python src\main.py --theme vt100
) else if exist "%~dp0SID-OS\src\main.py" (
    cd SID-OS
    python src\main.py --theme vt100
) else (
    echo  SID OS not found in this folder.
    echo  Run option [1] first to download it.
    pause
)
goto end

:update
echo.
echo  Updating SID OS...
python --version >nul 2>&1
if errorlevel 1 goto nopython
cd /d "%~dp0"
if exist "%~dp0get-sid.py" (
    python get-sid.py --update
) else (
    echo  Downloading bootstrap script...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/Ryuupyroxi/SID-OS/main/get-sid.py' -OutFile 'get-sid.py'}"
    python get-sid.py --update
)
goto end

:nopython
echo.
echo  ========================================
echo   Python is not installed on this system
echo  ========================================
echo.
echo  Windows does not include Python by default.
echo  To use SID OS, you need to install Python first:
echo.
echo  1. Go to: https://www.python.org/downloads/
echo  2. Download Python 3.8 or later
echo  3. Run the installer
echo  4. IMPORTANT: Check "Add Python to PATH"
echo  5. Open this script again after installing
echo.
echo  Opening Python download page...
start https://www.python.org/downloads/
echo.
pause
goto end

:about
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║           SID - Super Intelligent Distro          ║
echo  ║            v1.2.0 — For Old Hardware              ║
echo  ╚══════════════════════════════════════════════════╝
echo.
echo  SID is a lightweight CLI-based operating system for
echo  old hardware (4GB RAM target). AI is the primary
echo  interface - you navigate the OS by talking to it.
echo.
echo  Features:
echo  - AI-powered CLI interface
echo  - Works offline with local AI models
echo  - Voice control (requires whisper.cpp)
echo  - Retro computer themes (VT100, Apple II, C64...)
echo  - Web viewer with offline cache
echo  - Media player, image tools, file manager
echo  - Hardware benchmark & auto-optimization
echo  - Skills system for extending functionality
echo.
echo  Requirements: 2GB RAM (4GB recommended), 4GB disk
echo.
pause
goto end

:end
echo.
echo  Press any key to exit...
pause >nul
