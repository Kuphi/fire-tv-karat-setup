param([string]$Serial)
$ErrorActionPreference = 'Stop'
$device = @('-d')
if ($Serial) { $device = @('-s', $Serial) }
& adb @device shell pm enable --user 0 com.amazon.firehomestarter
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& adb @device shell pm enable --user 0 com.amazon.tv.launcher
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& adb @device shell pm enable --user 0 com.amazon.tv.launcher/.ui.HomeActivity_vNext
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& adb @device shell cmd package set-home-activity --user 0 com.amazon.tv.launcher/.ui.HomeActivity_vNext
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& adb @device shell am start -n com.amazon.tv.launcher/.ui.HomeActivity_vNext
exit $LASTEXITCODE
