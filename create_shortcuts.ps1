$WshShell = New-Object -ComObject WScript.Shell

$targetExe = "C:\src\chromium\src\out\thorium\selenium.exe"

# 1. Desktop shortcut
$desktopPath = [System.IO.Path]::Combine([System.Environment]::GetFolderPath('Desktop'), "Selenium.lnk")
$shortcut = $WshShell.CreateShortcut($desktopPath)
$shortcut.TargetPath = $targetExe
$shortcut.IconLocation = "$targetExe,0"
$shortcut.Save()
Write-Host "Created Desktop shortcut: $desktopPath"

# 2. Start Menu shortcut
$startMenuDir = [System.IO.Path]::Combine([System.Environment]::GetFolderPath('Programs'), "Selenium")
if (-not (Test-Path $startMenuDir)) {
    New-Item -ItemType Directory -Path $startMenuDir -Force | Out-Null
}
$startMenuPath = [System.IO.Path]::Combine($startMenuDir, "Selenium.lnk")
$shortcut2 = $WshShell.CreateShortcut($startMenuPath)
$shortcut2.TargetPath = $targetExe
$shortcut2.IconLocation = "$targetExe,0"
$shortcut2.Save()
Write-Host "Created Start Menu shortcut: $startMenuPath"

# 3. Refresh icon cache
& ie4uinit.exe -show
Write-Host "Icon cache refreshed."
