param(
    [string]$AppFile = "app.py",
    [string]$ShortcutName = "GeneradorCartas - Ejecutar (sin consola).lnk"
)

# Resolve full path of the app file relative to this script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$appPath = Resolve-Path (Join-Path $scriptDir $AppFile) -ErrorAction Stop

# Try to find pythonw.exe
$pythonwCmd = Get-Command pythonw.exe -ErrorAction SilentlyContinue
if ($pythonwCmd) {
    $pythonw = $pythonwCmd.Source
} else {
    # Fallback: try to locate python.exe and replace with pythonw.exe
    $pyCmd = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($pyCmd) {
        $pyExe = $pyCmd.Source
        $pythonwCandidate = [System.IO.Path]::Combine([System.IO.Path]::GetDirectoryName($pyExe), "pythonw.exe")
        if (Test-Path $pythonwCandidate) {
            $pythonw = $pythonwCandidate
        } else {
            Write-Error "No se encontró pythonw.exe en el sistema. Asegúrate de tener Python instalado y pythonw.exe en PATH."
            exit 1
        }
    } else {
        Write-Error "No se encontró python.exe ni pythonw.exe. Instala Python y vuelve a intentar."
        exit 1
    }
}

$desktop = [Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktop $ShortcutName

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $pythonw
$shortcut.Arguments = "`"$appPath`""
$shortcut.WorkingDirectory = Split-Path $appPath
$shortcut.IconLocation = $appPath
$shortcut.Save()

Write-Output "Shortcut creado en: $shortcutPath"