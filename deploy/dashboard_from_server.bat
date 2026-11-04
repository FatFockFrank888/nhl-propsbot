@echo off
rem Download the latest dashboard from the server and open it in your browser.
call "%~dp0server.cmd"
cd /d "%~dp0.."
if not exist output mkdir output
scp %SERVER%:%REMOTE_DIR%/output/dashboard.html output\server_dashboard.html
if errorlevel 1 (
  echo Could not download the dashboard - is SERVER set correctly in deploy\server.cmd?
  pause
  exit /b 1
)
start "" "output\server_dashboard.html"
