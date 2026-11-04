# Copies the bot's three secrets from this PC into GitHub Secrets for the nhl-propsbot repo.
# Values are read locally and sent straight to GitHub (encrypted); they are never printed.
$ErrorActionPreference = "Stop"
$gh = "C:\Program Files\GitHub CLI\gh.exe"
$repo = "FatFockFrank888/nhl-propsbot"

$values = @{}
$envFile = Join-Path $PSScriptRoot "..\.env"
if (Test-Path $envFile) {
    foreach ($line in Get-Content $envFile) {
        if ($line -match '^\s*([A-Z_]+)\s*=\s*(.+?)\s*$') { $values[$Matches[1]] = $Matches[2] }
    }
}
$odds = [Environment]::GetEnvironmentVariable("ODDS_API_KEY", "User")
if (-not $odds) { $odds = $env:ODDS_API_KEY }
if ($odds) { $values["ODDS_API_KEY"] = $odds }

$ok = 0
foreach ($name in "NTFY_TOPIC", "PINNACLE_API_KEY", "ODDS_API_KEY") {
    if (-not $values[$name]) { Write-Host "  MISSING: $name (not found on this PC)" -ForegroundColor Yellow; continue }
    $values[$name] | & $gh secret set $name -R $repo
    if ($LASTEXITCODE -eq 0) { Write-Host "  set $name" -ForegroundColor Green; $ok++ }
}
Write-Host ""
Write-Host "$ok of 3 secrets set on $repo."
& $gh secret list -R $repo
