param([switch]$NoLaunch,[switch]$TestMode)
$ErrorActionPreference = 'Stop'
$sourceRoot = [IO.Path]::GetFullPath($PSScriptRoot)
$package = Get-Content -LiteralPath (Join-Path $sourceRoot 'resources\app\package.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($package.name -ne 'codex-garden' -or $package.version -notmatch '^\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?$') { throw 'Invalid application package.' }
$hashes = Get-Content -LiteralPath (Join-Path $sourceRoot 'SHA256.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$sourceItems = Get-ChildItem -LiteralPath $sourceRoot -Recurse -Force
if ($sourceItems | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }) { throw 'Linked package files are not supported.' }
if (($sourceItems | Where-Object { -not $_.PSIsContainer }).Count -ne ($hashes.PSObject.Properties.Name.Count + 1)) { throw 'Unexpected files in package.' }
foreach ($entry in $hashes.PSObject.Properties) {
    $file = [IO.Path]::GetFullPath((Join-Path $sourceRoot $entry.Name))
    if (-not $file.StartsWith($sourceRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid package path.' }
    if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ne $entry.Value) { throw ('Package verification failed: ' + $entry.Name) }
}
if ($TestMode) { $programRoot = Join-Path ([IO.Path]::GetTempPath()) ('codex-garden-install-test-' + [Guid]::NewGuid().ToString('N')) }
else { $programRoot = Join-Path $env:LOCALAPPDATA 'Programs\QingyunGarden' }
$programRoot = [IO.Path]::GetFullPath($programRoot)
$marker = Join-Path $programRoot '.garden-install.json'
if ((Test-Path -LiteralPath $programRoot) -and -not (Test-Path -LiteralPath $marker)) { throw 'This directory is not a managed garden installation.' }
if (Test-Path -LiteralPath $marker) {
    $owner = Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json
    if ($owner.application -ne 'qingyun-garden') { throw 'Unexpected installation owner.' }
}
if (Test-Path -LiteralPath $programRoot) {
    $rootItems = @((Get-Item -LiteralPath $programRoot)) + @(Get-ChildItem -LiteralPath $programRoot -Recurse -Force)
    if ($rootItems | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }) { throw 'Linked installation directories are not supported.' }
}
if (-not $TestMode) {
    $existingKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\QingyunGardenBeta'
    if (Test-Path -LiteralPath $existingKey) {
        if ((Get-ItemProperty -LiteralPath $existingKey).InstallLocation -ne $programRoot) { throw 'Another installation owns the uninstall entry.' }
    }
}
$target = [IO.Path]::GetFullPath((Join-Path $programRoot ('versions\' + $package.version)))
if (-not $target.StartsWith($programRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid installation path.' }
if (Test-Path -LiteralPath $target) { throw 'This version is already installed. Exit it and start the installed application.' }
$staging = [IO.Path]::GetFullPath((Join-Path $programRoot ('staging\' + [Guid]::NewGuid().ToString('N'))))
if (-not $staging.StartsWith($programRoot + '\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid staging path.' }
New-Item -ItemType Directory -Path $staging -Force | Out-Null
@{application='qingyun-garden';schemaVersion=1} | ConvertTo-Json | Set-Content -LiteralPath $marker -Encoding UTF8
Get-ChildItem -LiteralPath $sourceRoot -Force | Copy-Item -Destination $staging -Recurse
foreach ($entry in $hashes.PSObject.Properties) {
    $copy = [IO.Path]::GetFullPath((Join-Path $staging $entry.Name))
    if (-not $copy.StartsWith($staging + '\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid copied path.' }
    if ((Get-FileHash -LiteralPath $copy -Algorithm SHA256).Hash -ne $entry.Value) { throw 'The copied package is incomplete.' }
}
New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
# Both absolute paths are validated under this installation root before the directory move.
Move-Item -LiteralPath $staging -Destination $target
Copy-Item -LiteralPath (Join-Path $sourceRoot 'Uninstall.ps1') -Destination (Join-Path $programRoot 'Uninstall.ps1')
$executable = Join-Path $target 'CodexGarden.exe'
if (-not $TestMode) {
    $shortcutPath = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Qingyun Garden.lnk'
    New-Item -ItemType Directory -Path (Split-Path -Parent $shortcutPath) -Force | Out-Null
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $executable
    $shortcut.WorkingDirectory = $target
    $shortcut.Description = 'Qingyun desktop garden'
    $shortcut.Save()
    $key = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\QingyunGardenBeta'
    New-Item -Path $key -Force | Out-Null
    New-ItemProperty -Path $key -Name DisplayName -Value 'Qingyun Garden' -PropertyType String -Force | Out-Null
    New-ItemProperty -Path $key -Name Publisher -Value 'risu1' -PropertyType String -Force | Out-Null
    New-ItemProperty -Path $key -Name DisplayVersion -Value $package.version -PropertyType String -Force | Out-Null
    New-ItemProperty -Path $key -Name InstallLocation -Value $programRoot -PropertyType String -Force | Out-Null
    $uninstall = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "' + (Join-Path $programRoot 'Uninstall.ps1') + '"'
    New-ItemProperty -Path $key -Name UninstallString -Value $uninstall -PropertyType String -Force | Out-Null
    if (-not $NoLaunch) { Start-Process -FilePath $executable -WorkingDirectory $target -WindowStyle Hidden }
}
Write-Output ('Installed: ' + $target)
if ($TestMode) { Write-Output 'Test mode: no shortcuts, registry entries, or application launch.' }
