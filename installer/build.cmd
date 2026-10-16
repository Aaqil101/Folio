@echo off
rem Builds the Folio Windows app and its installer (issue #14).
rem
rem Double-click, or call from a terminal. Extra arguments are forwarded to
rem build.ps1, e.g.:  build.cmd -AppOnly
rem
rem Flow: wipe build\+dist\ -> PyInstaller -> PAUSE (check the app, press r
rem to launch it) -> Inno Setup -> cleanup, leaving dist\installer\.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build.ps1" %*
echo.
pause
