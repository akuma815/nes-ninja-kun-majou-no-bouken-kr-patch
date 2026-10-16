@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0apply.ps1" -SourceRom "%~1" -OutputRom "%~2"
set "patch_exit=%ERRORLEVEL%"
if not defined NINJA_NO_PAUSE pause
exit /b %patch_exit%
