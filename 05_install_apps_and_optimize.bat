@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp005_install_apps_and_optimize.ps1" %*
exit /b %ERRORLEVEL%
