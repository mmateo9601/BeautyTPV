param([Parameter(Mandatory=$true)][string]$Instance)
$ErrorActionPreference = "Stop"
$python = Join-Path (Split-Path $PSScriptRoot) ".venv/Scripts/python.exe"
& $python "$PSScriptRoot/check.py" --instance $Instance
if ($LASTEXITCODE -ne 0) { throw "BeautyTPV: operación fallida ($LASTEXITCODE)" }
