param([ValidateSet('start','stop','setup','credentials','reset','rotate-users')][string]$Action = 'start')
$ErrorActionPreference = 'Stop'
try {
    $repoRoot = Split-Path -Parent $PSScriptRoot
    $demoPython = Join-Path $repoRoot '.venv\Scripts\pythonw.exe'
    if (-not (Test-Path -LiteralPath $demoPython -PathType Leaf)) {
        throw 'No se encuentra Python de .venv. Complete la instalacion inicial de docs/GUIA_WINDOWS_DEMO.md.'
    }
    $demoScript = Join-Path $PSScriptRoot 'windows_demo.py'
    $demoProcess = Start-Process -FilePath $demoPython -ArgumentList @(('"' + $demoScript + '"'), $Action) -WorkingDirectory $repoRoot -WindowStyle Hidden -PassThru
    # Start-Process -Wait waits the whole tree, including the persistent server.
    # Wait only for the launcher; habitual use must return after readiness.
    $demoProcess.WaitForExit()
    exit $demoProcess.ExitCode
} catch {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show($_.Exception.Message, 'BeautyTPV DEMO - Error', 'OK', 'Error') | Out-Null
    exit 1
}
