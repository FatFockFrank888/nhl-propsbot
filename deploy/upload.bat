@echo off
rem Copy the bot (code, settings, ledgers) from this PC to the server. Uses Windows' built-in ssh/scp.
call "%~dp0server.cmd"
if "%SERVER%"=="user@your-server-ip" (
  echo Edit deploy\server.cmd first: set SERVER=youruser@your-server-ip
  pause
  exit /b 1
)
cd /d "%~dp0.."
echo Uploading to %SERVER%:%REMOTE_DIR% ...
ssh %SERVER% "mkdir -p %REMOTE_DIR%"
scp -r propsbot deploy settings.json pyproject.toml README.md %SERVER%:%REMOTE_DIR%/
if exist data scp -r data %SERVER%:%REMOTE_DIR%/
if exist .env scp .env %SERVER%:%REMOTE_DIR%/
echo.
echo Uploaded. First time only, run on the server:
echo    ssh %SERVER%
echo    cd %REMOTE_DIR% ^&^& bash deploy/setup_server.sh
echo After later uploads:  ssh %SERVER% "sudo systemctl restart nhl-propsbot"
pause
