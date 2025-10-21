@echo off
REM PC Monitoring Client Installer
REM Run this as Administrator

echo ============================================================
echo PC Monitoring Client Installation
echo ============================================================
echo.

REM Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator!
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

echo [Step 1/3] Creating Scripts folder...
if not exist "C:\Scripts" mkdir "C:\Scripts"
echo OK - Folder created

echo.
echo [Step 2/3] Copying scripts...
copy /Y "%~dp0collect-info.ps1" "C:\Scripts\" >nul
copy /Y "%~dp0setup-schedule.ps1" "C:\Scripts\" >nul
echo OK - Scripts copied

echo.
echo [Step 3/3] Setting up scheduled task...
powershell -ExecutionPolicy Bypass -Command "& 'C:\Scripts\setup-schedule.ps1'"

echo.
echo ============================================================
echo Installation complete!
echo ============================================================
pause
