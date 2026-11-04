@echo off
rem NHL shots-on-goal edge bot: scans every few minutes and notifies live bets via ntfy.
cd /d "%~dp0"
python -m propsbot watch
pause
