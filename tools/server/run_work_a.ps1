param(
 [Parameter(Mandatory=$true)][string]$Repository,
 [Parameter(Mandatory=$true)][string]$Plan,
 [Parameter(Mandatory=$true)][string]$Output,
 [string]$Python='python'
)
$ErrorActionPreference='Stop'
Push-Location $Repository
try {
 & $Python -m tools.server.collect_daily_consumers --plan $Plan --output $Output
 if ($LASTEXITCODE -ne 0) { throw 'Daily source collection failed' }
 $m=Get-Content (Join-Path $Output 'manifest.json') -Raw | ConvertFrom-Json
 if ($m.missing -gt 0) { throw "Missing consumer sources: $($m.missing). See manifest.json; no semantic admission." }
 Write-Host 'All selected bytes verified. Package semantics, signs and time support require separate qualification.'
} finally { Pop-Location }
