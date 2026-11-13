param([string]$InstanceDirectory = "$env:LOCALAPPDATA\BeautyTPV")
$ErrorActionPreference = "Stop"
$python = Join-Path (Split-Path $PSScriptRoot) ".venv/Scripts/python.exe"
& python "$PSScriptRoot/install.py" --instance-dir $InstanceDirectory
if ($LASTEXITCODE -ne 0) { throw "BeautyTPV: operación fallida ($LASTEXITCODE)" }
