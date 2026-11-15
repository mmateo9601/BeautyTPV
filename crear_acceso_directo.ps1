param([string]$DesktopPath)
$ErrorActionPreference = 'Stop'
$repoRoot = $PSScriptRoot
$shell = New-Object -ComObject WScript.Shell
if (-not $DesktopPath) { $DesktopPath = $shell.SpecialFolders.Item('Desktop') }
if (-not (Test-Path -LiteralPath $DesktopPath -PathType Container)) { throw 'No se encuentra el escritorio de Windows.' }
$launcher = Join-Path $repoRoot 'scripts\demo_launcher.ps1'
$powershell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$entries = @(
    @{ Name = 'BeautyTPV DEMO'; Action = 'start'; Icon = 13 },
    @{ Name = 'Detener BeautyTPV DEMO'; Action = 'stop'; Icon = 27 },
    @{ Name = 'Usuarios BeautyTPV DEMO'; Action = 'credentials'; Icon = 44 },
    @{ Name = 'Reinicializar BeautyTPV DEMO'; Action = 'reset'; Icon = 238 },
    @{ Name = 'Cambiar usuarios BeautyTPV DEMO'; Action = 'rotate-users'; Icon = 44 }
)
foreach ($entry in $entries) {
    $linkPath = Join-Path $DesktopPath ($entry.Name + '.lnk')
    if (Test-Path -LiteralPath $linkPath) {
        $existing = $shell.CreateShortcut($linkPath)
        if ($existing.TargetPath -ne $powershell -or $existing.Arguments -notlike ('*' + $launcher + '*')) {
            throw ('Ya existe un acceso ajeno con ese nombre; no se sobrescribe: ' + $linkPath)
        }
    }
    $shortcut = $shell.CreateShortcut($linkPath)
    $shortcut.TargetPath = $powershell
    $shortcut.Arguments = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $launcher + '" -Action ' + $entry.Action
    $shortcut.WorkingDirectory = $repoRoot
    $shortcut.WindowStyle = 7
    $shortcut.IconLocation = (Join-Path $env:SystemRoot 'System32\shell32.dll') + ',' + $entry.Icon
    $shortcut.Description = 'BeautyTPV DEMO local: datos sinteticos, TEST, sin conexiones AEAT.'
    $shortcut.Save()
    Write-Output $linkPath
}
