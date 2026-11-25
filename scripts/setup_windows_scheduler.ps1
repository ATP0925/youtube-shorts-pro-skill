param(
    [string]$MorningTime = "19:30",
    [string]$NightTime = "22:45",
    [string]$TaskPrefix = "YTProShorts"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BatPath = Join-Path $ScriptDir "run_slot.bat"

$MName = "${TaskPrefix}_Morning_Slot"
if (Get-ScheduledTask -TaskName $MName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $MName -Confirm:$false
}
$TM = New-ScheduledTaskTrigger -Daily -At $MorningTime
$AM = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -WindowStyle Hidden -Command `"Start-Process -FilePath '$BatPath' -ArgumentList 'morning','--scheduled','--daily-ops' -WindowStyle Hidden -Wait`""
$SM = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 12)
Register-ScheduledTask -TaskName $MName -Trigger $TM -Action $AM -Settings $SM -Description "Automated Pro YouTube Shorts Morning Slot (--daily-ops)"

$NName = "${TaskPrefix}_Night_Slot"
if (Get-ScheduledTask -TaskName $NName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $NName -Confirm:$false
}
$TN = New-ScheduledTaskTrigger -Daily -At $NightTime
$AN = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -WindowStyle Hidden -Command `"Start-Process -FilePath '$BatPath' -ArgumentList 'night','--scheduled','--daily-ops' -WindowStyle Hidden -Wait`""
$SN = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 12)
Register-ScheduledTask -TaskName $NName -Trigger $TN -Action $AN -Settings $SN -Description "Automated Pro YouTube Shorts Night Slot (--daily-ops)"

Get-ScheduledTask -TaskName "${TaskPrefix}_*" | Select-Object TaskName, State, @{N='NextRunTime';E={(Get-ScheduledTaskInfo -TaskName $_.TaskName).NextRunTime}}
