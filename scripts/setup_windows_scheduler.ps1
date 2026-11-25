param(
    [string]$MorningTime = "19:30",
    [string]$NightTime = "22:45",
    [string]$TaskPrefix = "YTProShorts",
    [switch]$Help
)

function Show-Usage {
    Write-Host "YouTube Shorts Pro Skill — Windows Task Scheduler Setup" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\scripts\setup_windows_scheduler.ps1 [-MorningTime HH:mm] [-NightTime HH:mm] [-TaskPrefix Name] [-Help]"
    Write-Host ""
    Write-Host "Parameters:" -ForegroundColor Yellow
    Write-Host "  -MorningTime  Daily 24h time for Morning US slot (default: 19:30 IST = 9:00 AM EST)"
    Write-Host "  -NightTime    Daily 24h time for Night US slot   (default: 22:45 IST = 12:15 PM EST)"
    Write-Host "  -TaskPrefix   Prefix for scheduled task names    (default: YTProShorts)"
    Write-Host "  -Help         Show this help message and exit"
}

if ($Help) {
    Show-Usage
    exit 0
}

$TimePattern = '^([01]\d|2[0-3]):[0-5]\d$'
if ($MorningTime -notmatch $TimePattern) {
    Write-Host "ERROR: Invalid -MorningTime '$MorningTime'. Expected 24h format HH:mm (e.g. 19:30)." -ForegroundColor Red
    exit 1
}
if ($NightTime -notmatch $TimePattern) {
    Write-Host "ERROR: Invalid -NightTime '$NightTime'. Expected 24h format HH:mm (e.g. 22:45)." -ForegroundColor Red
    exit 1
}
if ([string]::IsNullOrWhiteSpace($TaskPrefix)) {
    Write-Host "ERROR: -TaskPrefix cannot be empty." -ForegroundColor Red
    exit 1
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BatPath = Join-Path $ScriptDir "run_slot.bat"
if (-not (Test-Path $BatPath)) {
    Write-Host "ERROR: Batch launcher not found at $BatPath" -ForegroundColor Red
    exit 1
}

Write-Host "Registering Windows Scheduled Tasks (prefix=$TaskPrefix)..." -ForegroundColor Cyan

$Slots = @(
    @{ Suffix = "Morning_Slot"; Arg = "morning"; Time = $MorningTime; Desc = "Automated Pro YouTube Shorts Morning Slot (--daily-ops)" },
    @{ Suffix = "Night_Slot";   Arg = "night";   Time = $NightTime;   Desc = "Automated Pro YouTube Shorts Night Slot (--daily-ops)" }
)

foreach ($s in $Slots) {
    $Name = "${TaskPrefix}_$($s.Suffix)"
    if (Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $Name -Confirm:$false
        Write-Host "  Replaced existing task: $Name" -ForegroundColor Yellow
    }

    $Trigger = New-ScheduledTaskTrigger -Daily -At $s.Time
    $Cmd = "Start-Process -FilePath '$BatPath' -ArgumentList '$($s.Arg)','--scheduled','--daily-ops' -WindowStyle Hidden -Wait"
    $Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -WindowStyle Hidden -Command `"$Cmd`""
    $Settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 12)

    Register-ScheduledTask -TaskName $Name -Trigger $Trigger -Action $Action -Settings $Settings -Description $s.Desc | Out-Null
    Write-Host "  Registered $Name at $($s.Time)" -ForegroundColor Green
}

Write-Host ""
Write-Host "Scheduled Tasks Status:" -ForegroundColor Cyan
Get-ScheduledTask -TaskName "${TaskPrefix}_*" | Select-Object TaskName, State, @{N = 'NextRunTime'; E = { (Get-ScheduledTaskInfo -TaskName $_.TaskName).NextRunTime } } | Format-Table -AutoSize
