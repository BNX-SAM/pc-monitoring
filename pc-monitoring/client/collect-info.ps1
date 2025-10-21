# PC Information Collection Script
# Run with Administrator privileges

param(
    [string]$ServerUrl = "http://localhost:5000/api/report"
)

# Script start log
Write-Host "=== PC Information Collection Started ===" -ForegroundColor Green

# 1. Collect basic system information
$computerName = $env:COMPUTERNAME
$userName = $env:USERNAME
$outlookDisplayName = $null
$ipAddress = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Ethernet*","Wi-Fi*" -ErrorAction SilentlyContinue | Select-Object -First 1).IPAddress

Write-Host "Computer Name: $computerName" -ForegroundColor Cyan
Write-Host "User Name (Windows): $userName" -ForegroundColor Cyan
Write-Host "IP Address: $ipAddress" -ForegroundColor Cyan

# 2. Collect storage information
Write-Host "`nCollecting storage information..." -ForegroundColor Yellow
$drives = Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Used -ne $null }
$driveInfo = @()

foreach ($drive in $drives) {
    $totalGB = [math]::Round($drive.Used / 1GB + $drive.Free / 1GB, 2)
    $usedGB = [math]::Round($drive.Used / 1GB, 2)
    $freeGB = [math]::Round($drive.Free / 1GB, 2)
    $usedPercent = [math]::Round(($usedGB / $totalGB) * 100, 1)

    $driveInfo += @{
        drive = $drive.Name + ":"
        total_gb = $totalGB
        used_gb = $usedGB
        free_gb = $freeGB
        used_percent = $usedPercent
    }

    Write-Host "  $($drive.Name): Total: ${totalGB}GB / Used: ${usedGB}GB / Free: ${freeGB}GB (${usedPercent}%)" -ForegroundColor White
}

# 3. Collect Outlook PST file information
Write-Host "`nSearching for Outlook PST files..." -ForegroundColor Yellow
$pstFiles = @()
$totalPstSize = 0

# Common PST file locations
$pstLocations = @(
    "$env:USERPROFILE\Documents\Outlook Files",
    "$env:LOCALAPPDATA\Microsoft\Outlook",
    "$env:APPDATA\Local\Microsoft\Outlook",
    "$env:USERPROFILE\AppData\Local\Microsoft\Outlook"
)

foreach ($location in $pstLocations) {
    if (Test-Path $location) {
        $files = Get-ChildItem -Path $location -Filter "*.pst" -Recurse -ErrorAction SilentlyContinue
        foreach ($file in $files) {
            $sizeGB = [math]::Round($file.Length / 1GB, 2)
            $pstFiles += @{
                name = $file.Name
                path = $file.FullName
                size_gb = $sizeGB
                last_modified = $file.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
            }
            $totalPstSize += $sizeGB
            Write-Host "  Found: $($file.Name) - ${sizeGB}GB" -ForegroundColor White
        }
    }
}

if ($pstFiles.Count -eq 0) {
    Write-Host "  No PST files found." -ForegroundColor Gray
}

# 4. Collect Outlook mail information and active accounts
Write-Host "`nCollecting Outlook mail information..." -ForegroundColor Yellow
$mailInfo = @{
    total_emails = 0
    period_emails = 0
    inbox_size_mb = 0
    last_archive_date = $null
    status = "not_available"
}
$activeEmailAccounts = @()

try {
    # Try to create Outlook COM object
    $outlook = New-Object -ComObject Outlook.Application
    $namespace = $outlook.GetNamespace("MAPI")

    # Collect active email accounts
    Write-Host "  Collecting email accounts..." -ForegroundColor Cyan
    foreach ($account in $outlook.Session.Accounts) {
        $accountInfo = @{
            display_name = $account.DisplayName
            email_address = $account.SmtpAddress
            account_type = $account.AccountType
        }
        $activeEmailAccounts += $accountInfo
        Write-Host "    - $($account.DisplayName) ($($account.SmtpAddress))" -ForegroundColor Gray

        # Use first account's display name as the Outlook user name
        if ($outlookDisplayName -eq $null -and $account.DisplayName) {
            # Extract just the name part (before any parentheses or extra info)
            $displayNameParts = $account.DisplayName -split '\('
            $outlookDisplayName = $displayNameParts[0].Trim()
            Write-Host "  Using Outlook name: $outlookDisplayName" -ForegroundColor Cyan
        }
    }

    # Check for Archive folders and last archive date
    Write-Host "  Checking archive information..." -ForegroundColor Cyan
    try {
        foreach ($store in $namespace.Stores) {
            $storeName = $store.DisplayName.ToLower()

            # Check if this is an archive store
            if ($storeName -contains "archive" -or $storeName -contains "보관" -or
                $store.FilePath -like "*archive*" -or $store.FilePath -like "*보관*") {

                Write-Host "    Found archive: $($store.DisplayName)" -ForegroundColor Gray

                # Try to get the root folder of the archive
                try {
                    $archiveRoot = $store.GetRootFolder()

                    # Get all folders in archive
                    $allFolders = @($archiveRoot)
                    for ($i = 0; $i -lt $archiveRoot.Folders.Count; $i++) {
                        $allFolders += $archiveRoot.Folders.Item($i + 1)
                    }

                    # Find the most recent item in archive to determine last archive date
                    $mostRecentDate = $null
                    foreach ($folder in $allFolders) {
                        try {
                            if ($folder.Items.Count -gt 0) {
                                # Sort by received time and get the most recent
                                $folder.Items.Sort("[ReceivedTime]", $true)
                                $newestItem = $folder.Items.Item(1)

                                if ($newestItem.ReceivedTime) {
                                    if ($mostRecentDate -eq $null -or $newestItem.ReceivedTime -gt $mostRecentDate) {
                                        $mostRecentDate = $newestItem.ReceivedTime
                                    }
                                }
                            }
                        } catch {
                            # Skip folders that can't be accessed
                        }
                    }

                    if ($mostRecentDate) {
                        $mailInfo.last_archive_date = $mostRecentDate.ToString("yyyy-MM-dd HH:mm:ss")
                        Write-Host "    Last archived item: $($mostRecentDate.ToString('yyyy-MM-dd'))" -ForegroundColor Cyan
                    }

                    # Release folder objects
                    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($archiveRoot) | Out-Null
                } catch {
                    Write-Host "    Could not access archive folder details" -ForegroundColor Yellow
                }
            }
        }
    } catch {
        Write-Host "  Warning: Could not check archive information" -ForegroundColor Yellow
    }

    # Access inbox
    $inbox = $namespace.GetDefaultFolder(6) # 6 = olFolderInbox

    if ($inbox) {
        $mailInfo.status = "success"
        $mailInfo.total_emails = $inbox.Items.Count

        # Calculate Toronto timezone email count (Yesterday 7PM - Today 8AM Toronto time)
        # Toronto is EST (UTC-5) or EDT (UTC-4) depending on daylight saving
        try {
            $torontoTZ = [System.TimeZoneInfo]::FindSystemTimeZoneById("Eastern Standard Time")
            $nowToronto = [System.TimeZoneInfo]::ConvertTime([DateTime]::Now, $torontoTZ)

            # Yesterday 19:00 Toronto time
            $startTime = $nowToronto.Date.AddDays(-1).AddHours(17)
            # Today 08:00 Toronto time
            $endTime = $nowToronto.Date.AddHours(8)

            # Convert to local time for comparison
            $localTZ = [System.TimeZoneInfo]::Local
            $startTimeLocal = [System.TimeZoneInfo]::ConvertTime($startTime, $torontoTZ, $localTZ)
            $endTimeLocal = [System.TimeZoneInfo]::ConvertTime($endTime, $torontoTZ, $localTZ)

            Write-Host "  Counting emails from $($startTimeLocal.ToString('yyyy-MM-dd HH:mm')) to $($endTimeLocal.ToString('yyyy-MM-dd HH:mm'))" -ForegroundColor Cyan
            Write-Host "  (Toronto Yesterday 7PM - Today 8AM)" -ForegroundColor Cyan

            $periodEmails = $inbox.Items | Where-Object {
                $_.ReceivedTime -and
                $_.ReceivedTime -ge $startTimeLocal -and
                $_.ReceivedTime -lt $endTimeLocal
            }
            $mailInfo.period_emails = ($periodEmails | Measure-Object).Count
        } catch {
            Write-Host "  Warning: Could not calculate Toronto timezone. Using system time." -ForegroundColor Yellow
            # Fallback to today's emails
            $today = Get-Date -Format "yyyy-MM-dd"
            $todayEmails = $inbox.Items | Where-Object {
                $_.ReceivedTime -and
                (Get-Date $_.ReceivedTime -Format "yyyy-MM-dd") -eq $today
            }
            $mailInfo.period_emails = ($todayEmails | Measure-Object).Count
        }

        # Inbox size approximate
        $mailInfo.inbox_size_mb = [math]::Round($inbox.Items.Count * 0.05, 2) # Average 50KB per email

        Write-Host "  Total emails: $($mailInfo.total_emails)" -ForegroundColor White
        Write-Host "  Period emails: $($mailInfo.period_emails)" -ForegroundColor White
        Write-Host "  Inbox size (estimated): $($mailInfo.inbox_size_mb)MB" -ForegroundColor White
    }

    # Release COM objects
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($namespace) | Out-Null
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($outlook) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()

} catch {
    $mailInfo.status = "error"
    Write-Host "  Cannot access Outlook. Make sure Outlook is installed and running." -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
}

# 5. Package data
# Use Outlook display name if available, otherwise use Windows username
$finalUserName = if ($outlookDisplayName) { $outlookDisplayName } else { $userName }

Write-Host "`nFinal user name: $finalUserName" -ForegroundColor Green

$reportData = @{
    computer_name = $computerName
    user_name = $finalUserName
    windows_user = $userName
    ip_address = $ipAddress
    timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    drives = $driveInfo
    pst_files = $pstFiles
    total_pst_size_gb = [math]::Round($totalPstSize, 2)
    mail_info = $mailInfo
    active_email_accounts = $activeEmailAccounts
    last_archive_date = $mailInfo.last_archive_date
}

$jsonData = $reportData | ConvertTo-Json -Depth 10

# 6. Send to server
Write-Host "`nSending data to server..." -ForegroundColor Yellow
Write-Host "Server URL: $ServerUrl" -ForegroundColor Cyan

try {
    $response = Invoke-RestMethod -Uri $ServerUrl -Method Post -Body $jsonData -ContentType "application/json; charset=utf-8"
    Write-Host "[SUCCESS] Data sent successfully!" -ForegroundColor Green
    Write-Host "Server response: $($response.message)" -ForegroundColor Green
} catch {
    Write-Host "[FAILED] Data transmission failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red

    # Save locally if transmission fails
    $localLogPath = "$env:TEMP\pc-info-report.json"
    $jsonData | Out-File -FilePath $localLogPath -Encoding UTF8
    Write-Host "Data saved locally: $localLogPath" -ForegroundColor Yellow
}

Write-Host "`n=== Collection Complete ===" -ForegroundColor Green
