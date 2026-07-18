param(
    [string]$TargetFile = "ejecutar.bat",
    [string]$ShortcutName = "GeneradorCartas - Ejecutar.lnk"
)

# Resolve full path of the target file relative to this script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$targetPath = Resolve-Path (Join-Path $scriptDir $TargetFile) -ErrorAction Stop

$desktop = [Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktop $ShortcutName

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetPath
$shortcut.WorkingDirectory = Split-Path $targetPath
$shortcut.IconLocation = $targetPath
$shortcut.Save()

Write-Output "Shortcut created: $shortcutPath"