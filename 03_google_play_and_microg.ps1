& "$PSScriptRoot/tools/launch.ps1" -Flow root -ForwardArgs (@('--root-phase','google') + $args)
exit $LASTEXITCODE
