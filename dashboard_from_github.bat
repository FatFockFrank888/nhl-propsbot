@echo off
rem Download the dashboard the GitHub Actions bot last wrote, and open it.
rem Edit the next line once: your GitHub username / repository name.
set GITHUB_REPO=your-username/nhl-propsbot
cd /d "%~dp0"
if "%GITHUB_REPO%"=="your-username/nhl-propsbot" (
  echo Edit dashboard_from_github.bat first: set GITHUB_REPO=yourname/yourrepo
  pause
  exit /b 1
)
if not exist output mkdir output
curl -fsSL -o output\github_dashboard.html "https://raw.githubusercontent.com/%GITHUB_REPO%/bot-data/output/dashboard.html"
if errorlevel 1 (
  echo Could not download. Is the repository public and has the bot run at least once?
  pause
  exit /b 1
)
start "" "output\github_dashboard.html"
