$ErrorActionPreference = 'Stop'
$expected = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'Programs\QingyunGarden'))
$target = [IO.Path]::GetFullPath($PSScriptRoot).TrimEnd('\')
if (-not [string]::Equals($target,$expected.TrimEnd('\'),[StringComparison]::OrdinalIgnoreCase)) { throw 'Unexpected uninstall directory. No files were removed.' }
$marker = Join-Path $target '.garden-install.json'
if (-not (Test-Path -LiteralPath $marker)) { throw 'Installation marker is missing. No files were removed.' }
if ((Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json).application -ne 'qingyun-garden') { throw 'Unexpected installation owner.' }
$items = @((Get-Item -LiteralPath $target)) + @(Get-ChildItem -LiteralPath $target -Recurse -Force)
if ($items | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }) { throw 'Linked installation directories are not supported. No files were removed.' }
$running = Get-Process -Name CodexGarden -ErrorAction SilentlyContinue | Where-Object { $_.Path -and $_.Path.StartsWith($target + '\',[StringComparison]::OrdinalIgnoreCase) }
if ($running) { throw 'Please exit Qingyun Garden from its tray menu before uninstalling.' }
$shortcutPath = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Qingyun Garden.lnk'
if (Test-Path -LiteralPath $shortcutPath) {
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    if ($shortcut.TargetPath.StartsWith($target + '\',[StringComparison]::OrdinalIgnoreCase)) { Remove-Item -LiteralPath $shortcutPath }
}
$key = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\QingyunGardenBeta'
if (Test-Path -LiteralPath $key) {
    if ((Get-ItemProperty -LiteralPath $key).InstallLocation -ne $target) { throw 'Uninstall entry belongs to another installation.' }
    Remove-Item -LiteralPath $key -Recurse
}
# Target is the exact per-user application directory verified above. Collection and preferences are outside it.
Remove-Item -LiteralPath $target -Recurse
Write-Output 'Application removed. Your collection and preferences were preserved.'
