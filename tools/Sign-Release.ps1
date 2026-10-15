param([Parameter(Mandatory=$true)][string]$Thumbprint,[Parameter(Mandatory=$true)][string]$ReleaseRoot,[Parameter(Mandatory=$true)][string]$TimestampUrl)
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\dist')).TrimEnd('\')
$release=[IO.Path]::GetFullPath($ReleaseRoot).TrimEnd('\')
if (-not $release.StartsWith($workspace+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Signing root must be inside this project dist directory.' }
if ($TimestampUrl -notmatch '^https://') { throw 'Use an HTTPS RFC3161 timestamp service supplied by your certificate issuer.' }
$cert=Get-Item -LiteralPath ('Cert:\CurrentUser\My\'+$Thumbprint)
if (-not $cert.HasPrivateKey -or $cert.NotAfter -lt (Get-Date) -or -not ($cert.EnhancedKeyUsageList.ObjectId -contains '1.3.6.1.5.5.7.3.3')) { throw 'A current code-signing certificate with private key is required.' }
$signTool=(Get-Command signtool.exe -ErrorAction Stop).Source
$files=Get-ChildItem -LiteralPath $release -Recurse -File | Where-Object { $_.Name -in @('CodexGarden.exe','garden-bridge.exe','garden-mcp.exe') }
if (-not $files) { throw 'No garden executables found.' }
foreach ($file in $files) {
    & $signTool sign /sha1 $Thumbprint /fd SHA256 /tr $TimestampUrl /td SHA256 $file.FullName
    if ($LASTEXITCODE -ne 0) { throw 'Signing failed.' }
    if ((Get-AuthenticodeSignature -LiteralPath $file.FullName).Status -ne 'Valid') { throw 'Signature verification failed.' }
}
Write-Output 'Signed. Regenerate all SHA256 manifests and archives before distribution.'
