param([string]$Flow, [string[]]$ForwardArgs)
$ErrorActionPreference = 'Stop'
function Get-SetupMessage {
    param([string]$English, [string]$German)
    if ($env:FIRE_TV_LANG -eq 'de') { return $German }
    return $English
}

# Select language before installing dependencies.
for ($i = 0; $i -lt $ForwardArgs.Count; $i++) {
    if ($ForwardArgs[$i] -eq '--lang') {
        if ($i + 1 -ge $ForwardArgs.Count) { throw '--lang requires en or de / --lang benötigt en oder de' }
        $i += 1
        $env:FIRE_TV_LANG = $ForwardArgs[$i]
    } elseif ($ForwardArgs[$i] -like '--lang=*') { $env:FIRE_TV_LANG = $ForwardArgs[$i].Substring(7) }
}
if (-not $env:FIRE_TV_LANG) {
    if ([Console]::IsInputRedirected) { $env:FIRE_TV_LANG = 'en' }
    else {
        Write-Host "`nChoose language / Sprache wählen`n[1] English`n[2] Deutsch`nEXIT = exit / beenden"
        while (-not $env:FIRE_TV_LANG) {
            $choice = Read-Host '1 / 2'
            switch ($choice.ToLower()) {
                '1' { $env:FIRE_TV_LANG = 'en' }
                'en' { $env:FIRE_TV_LANG = 'en' }
                '2' { $env:FIRE_TV_LANG = 'de' }
                'de' { $env:FIRE_TV_LANG = 'de' }
                'exit' { exit 0 }
                default { Write-Host 'Please choose 1 or 2 / Bitte 1 oder 2 wählen.' }
            }
        }
    }
}
if ($env:FIRE_TV_LANG -notin @('en', 'de')) { throw 'Language must be en or de / Sprache muss en oder de sein' }
$env:PYTHONDONTWRITEBYTECODE = '1'
$base = Split-Path $PSScriptRoot -Parent
$env:Path = "$base/tools/platform-tools;" + $env:Path
if ($ForwardArgs -notcontains '--dry-run' -and $ForwardArgs -notcontains '--preview-only') { & "$PSScriptRoot/install-dependencies.ps1" }
$engine = "$base/karat-automation/karat.py"
$engineArgs = @($Flow, '--base', $base) + $ForwardArgs
if ($Flow -eq 'apps') { $engine = "$base/karat-automation/install_apps_and_optimize.py"; $engineArgs = @('--base', $base) + $ForwardArgs }
if ($Flow -eq 'menu') { $engine = "$base/karat-automation/setup_menu.py"; $engineArgs = @('--base', $base) + $ForwardArgs }
if (Get-Command py -ErrorAction SilentlyContinue) { & py -3 $engine @engineArgs }
elseif (Get-Command python -ErrorAction SilentlyContinue) { & python $engine @engineArgs }
else { throw (Get-SetupMessage 'Python was installed. Open a new terminal and run again.' 'Python wurde installiert. Neues Terminal öffnen und erneut starten.') }
exit $LASTEXITCODE
