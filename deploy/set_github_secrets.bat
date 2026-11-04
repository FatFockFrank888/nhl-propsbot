@echo off
rem Double-click: copies NTFY_TOPIC, PINNACLE_API_KEY and ODDS_API_KEY from this PC into GitHub Secrets.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0set_github_secrets.ps1"
pause
