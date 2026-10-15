@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp001_temporary_root_and_disable_ota.ps1" %*
exit /b %ERRORLEVEL%
