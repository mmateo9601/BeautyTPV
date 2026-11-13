param([Parameter(Mandatory=$true)][string]$Instance)
$ErrorActionPreference = "Stop"
$instancePath = (Resolve-Path -LiteralPath $Instance).Path
$startScript = Join-Path $PSScriptRoot "start.ps1"
$arguments = '-NoProfile -WindowStyle Hidden -File "' + $startScript + '" -Instance "' + $instancePath + '"'
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arguments
$trigger = New-ScheduledTaskTrigger -AtLogOn -User ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name)
$settings = New-ScheduledTaskSettingsSet -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero)
Register-ScheduledTask -TaskName "BeautyTPV-Local" -Action $action -Trigger $trigger -Settings $settings -Description "BeautyTPV local: servidor y workers de la empresa" -Force
