& "$PSScriptRoot/tools/launch.ps1" -Flow root -ForwardArgs (@('--root-phase','temporary') + $args)
exit $LASTEXITCODE
