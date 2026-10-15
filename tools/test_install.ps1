param([string]$PackagePath)
$ErrorActionPreference='Stop'
$key='HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\QingyunGardenBeta'
if (Test-Path -LiteralPath $key) { throw 'A real installation exists; isolated lifecycle test will not touch its registry entry.' }
$scratch=Join-Path ([IO.Path]::GetTempPath()) ('garden-lifecycle-'+[Guid]::NewGuid().ToString('N'))
$oldLocal=$env:LOCALAPPDATA; $oldRoaming=$env:APPDATA
try {
    $env:LOCALAPPDATA=Join-Path $scratch 'Local';$env:APPDATA=Join-Path $scratch 'Roaming'
    & (Join-Path $PackagePath 'Install.ps1') -NoLaunch
    if ($LASTEXITCODE) { throw 'Install failed.' }
    $root=Join-Path $env:LOCALAPPDATA 'Programs\QingyunGarden'
    $entry=Get-ItemProperty -LiteralPath $key
    if ($entry.InstallLocation -ne $root -or $entry.Publisher -ne 'risu1') { throw 'Uninstall registration mismatch.' }
    $shortcut=Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Qingyun Garden.lnk'
    if (-not (Test-Path -LiteralPath $shortcut)) { throw 'Start menu shortcut missing.' }
    $preserved=Join-Path $env:APPDATA 'codex-garden-pet-v06\sentinel.txt'
    New-Item -ItemType Directory -Path (Split-Path $preserved) -Force | Out-Null
    Set-Content -LiteralPath $preserved -Value 'keep'
    & (Join-Path $root 'Uninstall.ps1')
    if ((Test-Path -LiteralPath $root) -or (Test-Path -LiteralPath $shortcut) -or (Test-Path -LiteralPath $key)) { throw 'Uninstall left application registration behind.' }
    if (-not (Test-Path -LiteralPath $preserved)) { throw 'User settings were removed.' }
    @{passed=$true;install=$true;shortcut=$true;registration=$true;uninstall=$true;settingsPreserved=$true;scratch=$scratch} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot '..\verification\rc010-install-lifecycle.json') -Encoding UTF8
    Write-Output 'Isolated install, Start menu, registry and uninstall lifecycle passed.'
} finally { $env:LOCALAPPDATA=$oldLocal;$env:APPDATA=$oldRoaming }
