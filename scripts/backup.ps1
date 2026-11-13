param([Parameter(Mandatory=$true)][string]$Instance, [Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference = "Stop"
$python = Join-Path (Split-Path $PSScriptRoot) ".venv/Scripts/python.exe"
& $python "$PSScriptRoot/backup.py" --instance $Instance --output $Output
if ($LASTEXITCODE -ne 0) { throw "BeautyTPV: operación fallida ($LASTEXITCODE)" }
