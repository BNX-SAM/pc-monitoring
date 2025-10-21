# Setup PC Monitoring Scheduled Task
# Run this script as Administrator

Write-Host "Setting up PC Monitoring scheduled task..." -ForegroundColor Green
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click on PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    pause
    exit 1
}

# Server URL - modify this if your server IP is different
$serverUrl = "http://192.168.2.76:5000/api/report"

Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  Script Path: C:\Scripts\collect-info.ps1"
Write-Host "  Server URL: $serverUrl"
Write-Host "  Schedule: Daily at 12:00 PM"
Write-Host ""

# Create scheduled task
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-WindowStyle Hidden -ExecutionPolicy Bypass -File `"C:\Scripts\collect-info.ps1`" -ServerUrl `"$serverUrl`""

$trigger = New-ScheduledTaskTrigger -Daily -At "12:00PM"

$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive -RunLevel Highest

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

# Register the task
try {
    Register-ScheduledTask -TaskName "PC Monitoring Collection" `
        -Action $action `
        -Trigger $trigger `
        -Principal $principal `
        -Settings $settings `
        -Description "Collects PC information and sends to monitoring server - runs daily at 12:00 PM" `
        -Force

    Write-Host "[SUCCESS] Scheduled task created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:" -ForegroundColor Cyan
    Write-Host "  Name: PC Monitoring Collection"
    Write-Host "  Schedule: Every day at 12:00 PM"
    Write-Host "  Status: Enabled"
    Write-Host ""
    Write-Host "You can manage this task in Task Scheduler (taskschd.msc)" -ForegroundColor Yellow
    Write-Host ""

    # Ask if user wants to test run now
    $test = Read-Host "Do you want to test run the task now? (Y/N)"
    if ($test -eq "Y" -or $test -eq "y") {
        Write-Host "Running task now..." -ForegroundColor Yellow
        Start-ScheduledTask -TaskName "PC Monitoring Collection"
        Write-Host "Task started! Check the server dashboard." -ForegroundColor Green
    }

} catch {
    Write-Host "[FAILED] Error creating scheduled task!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
pause
