param([Parameter(Mandatory=$true)][string]$Instance, [Parameter(Mandatory=$true)][string]$Archive, [Parameter(Mandatory=$true)][string]$Confirm)
$ErrorActionPreference = "Stop"
$python = Join-Path (Split-Path $PSScriptRoot) ".venv/Scripts/python.exe"
& $python "$PSScriptRoot/restore.py" --instance $Instance --archive $Archive --offline --confirm $Confirm
if ($LASTEXITCODE -ne 0) { throw "BeautyTPV: operación fallida ($LASTEXITCODE)" }
