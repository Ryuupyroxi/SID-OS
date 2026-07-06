@echo off
REM SID OS Test Suite for Windows
cd /d "%~dp0"
python test_sid.py %*
pause
