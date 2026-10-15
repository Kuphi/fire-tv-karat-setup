$ErrorActionPreference = 'Stop'
function Get-SetupMessage {
    param([string]$English, [string]$German)
    if ($env:FIRE_TV_LANG -eq 'de') { return $German }
    return $English
}

$base = Split-Path $PSScriptRoot -Parent
if (-not (Get-Command py -ErrorAction SilentlyContinue) -and -not (Get-Command python -ErrorAction SilentlyContinue)) {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) { throw (Get-SetupMessage 'Install Python >=3.10: https://www.python.org/downloads/windows/ (enable PATH), then run again.' 'Python >=3.10 installieren: https://www.python.org/downloads/windows/ (PATH aktivieren), danach erneut starten.') }
    winget install --id Python.Python.3.13 --exact --scope user --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) { throw (Get-SetupMessage 'Python installation failed.' 'Python-Installation fehlgeschlagen.') }
    $env:Path = [Environment]::GetEnvironmentVariable('Path','User') + ';' + [Environment]::GetEnvironmentVariable('Path','Machine')
}
if (-not (Get-Command adb -ErrorAction SilentlyContinue) -and -not (Test-Path "$base/tools/platform-tools/adb.exe")) {
    $zip = Join-Path $PSScriptRoot 'platform-tools-download.zip'
    $url = 'https://dl.google.com/android/repository/platform-tools-latest-windows.zip'
    if (Get-Command wget.exe -ErrorAction SilentlyContinue) {
        & wget.exe --https-only -O $zip $url
        if ($LASTEXITCODE -ne 0) { throw (Get-SetupMessage 'ADB download failed.' 'ADB-Download fehlgeschlagen.') }
    } else { Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing }
    Expand-Archive -Path $zip -DestinationPath $PSScriptRoot -Force
    Remove-Item $zip
}
$env:Path = "$base/tools/platform-tools;" + $env:Path
Write-Host (Get-SetupMessage '[OK] Python and Android Platform Tools are ready. Install USB drivers separately if needed.' '[OK] Python und Android Platform Tools vorbereitet. USB-Treiber bei Bedarf separat installieren.') -ForegroundColor Green
