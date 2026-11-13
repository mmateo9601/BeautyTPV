param([Parameter(Mandatory=$true)][string]$Instance, [string]$HostName = "127.0.0.1", [int]$Port = 8000, [switch]$Development)
$ErrorActionPreference = "Stop"
$python = Join-Path (Split-Path $PSScriptRoot) ".venv/Scripts/python.exe"
$extra = @()
if ($Development) { $extra += "--development" }
& $python "$PSScriptRoot/service.py" --instance $Instance --host $HostName --port $Port @extra
if ($LASTEXITCODE -ne 0) { throw "BeautyTPV: operación fallida ($LASTEXITCODE)" }
