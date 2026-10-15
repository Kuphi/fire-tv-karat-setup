& "$PSScriptRoot/tools/launch.ps1" -Flow root -ForwardArgs (@('--root-phase','permanent') + $args)
exit $LASTEXITCODE
