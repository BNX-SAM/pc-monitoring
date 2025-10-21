# Quick Install Script for PC Monitoring
# Can be run directly from SMB share
# Usage: powershell -ExecutionPolicy Bypass -File "\\server\share\client\quick-install.ps1"

param(
    [string]$ServerUrl = "http://192.168.2.76:5000/api/report"
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "PC Monitoring Client - Quick Install" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check for admin privileges
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click on PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host "Then run:" -ForegroundColor Yellow
    Write-Host "  powershell -ExecutionPolicy Bypass -File ""$PSCommandPath""" -ForegroundColor White
    pause
    exit 1
}

# Get the directory where this script is located
$scriptDir = Split-Path -Parent $PSCommandPath

Write-Host "[Step 1/3] Creating C:\Scripts folder..." -ForegroundColor Yellow
if (-not (Test-Path "C:\Scripts")) {
    New-Item -Path "C:\Scripts" -ItemType Directory -Force | Out-Null
}
Write-Host "  OK - Folder ready" -ForegroundColor Green

Write-Host ""
Write-Host "[Step 2/3] Copying scripts from $scriptDir..." -ForegroundColor Yellow

# Copy collect-info.ps1
if (Test-Path "$scriptDir\collect-info.ps1") {
    Copy-Item "$scriptDir\collect-info.ps1" -Destination "C:\Scripts\" -Force
    Write-Host "  OK - collect-info.ps1 copied" -ForegroundColor Green
} else {
    Write-Host "  ERROR - collect-info.ps1 not found!" -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "[Step 3/3] Setting up scheduled task..." -ForegroundColor Yellow
Write-Host "  Server URL: $ServerUrl" -ForegroundColor Cyan
Write-Host "  Schedule: Daily at 12:00 PM" -ForegroundColor Cyan

# Create scheduled task
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-WindowStyle Hidden -ExecutionPolicy Bypass -File `"C:\Scripts\collect-info.ps1`" -ServerUrl `"$ServerUrl`""

$trigger = New-ScheduledTaskTrigger -Daily -At "12:00PM"

$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive -RunLevel Highest

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

try {
    Register-ScheduledTask -TaskName "PC Monitoring Collection" `
        -Action $action `
        -Trigger $trigger `
        -Principal $principal `
        -Settings $settings `
        -Description "Collects PC information and sends to monitoring server - runs daily at 12:00 PM" `
        -Force | Out-Null

    Write-Host "  OK - Scheduled task created" -ForegroundColor Green
} catch {
    Write-Host "  ERROR - Failed to create scheduled task" -ForegroundColor Red
    Write-Host "  $($_.Exception.Message)" -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  Computer: $env:COMPUTERNAME" -ForegroundColor White
Write-Host "  Task Name: PC Monitoring Collection" -ForegroundColor White
Write-Host "  Schedule: Daily at 12:00 PM" -ForegroundColor White
Write-Host "  Server: $ServerUrl" -ForegroundColor White
Write-Host ""

# Ask if user wants to test run
$test = Read-Host "Do you want to test run now? (Y/N)"
if ($test -eq "Y" -or $test -eq "y") {
    Write-Host ""
    Write-Host "Running test..." -ForegroundColor Yellow
    Start-ScheduledTask -TaskName "PC Monitoring Collection"
    Start-Sleep -Seconds 2
    Write-Host "Test started! Check the server dashboard at http://192.168.2.76:5000" -ForegroundColor Green
}

Write-Host ""
Write-Host "Press any key to exit..."
pause | Out-Null
