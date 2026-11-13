param([Parameter(Mandatory=$true)][string]$Instance, [Parameter(Mandatory=$true)][string]$Package, [Parameter(Mandatory=$true)][string]$Sha256)
$ErrorActionPreference = "Stop"
$python = Join-Path (Split-Path $PSScriptRoot) ".venv/Scripts/python.exe"
& $python "$PSScriptRoot/update.py" --instance $Instance --package $Package --sha256 $Sha256 --offline
if ($LASTEXITCODE -ne 0) { throw "BeautyTPV: operación fallida ($LASTEXITCODE)" }
