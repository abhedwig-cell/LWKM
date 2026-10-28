param(
  [Parameter(Mandatory=$true)][string[]]$Roots,
  [string]$ReportDir = ".\SWP_recovery_audit",
  [int]$Expected = 0,
  [string]$HruIdsCsv,
  [switch]$Package
)
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
if (-not $HruIdsCsv -and $Expected -le 0) { throw "Provide release-specific -HruIdsCsv or -Expected" }
$targetIds = @()
if ($HruIdsCsv) {
  if (-not (Test-Path -LiteralPath $HruIdsCsv)) { throw "HRU IDs CSV not found" }
  $targetIds = @(Import-Csv -LiteralPath $HruIdsCsv | ForEach-Object {
    if ($_.PSObject.Properties.Name -contains 'hru') { [int]$_.hru }
    elseif ($_.PSObject.Properties.Name -contains 'hru_id') { [int]$_.hru_id }
    else { throw "Missing hru/hru_id column" }
  } | Sort-Object -Unique)
  if ($targetIds.Count -eq 0 -or @($targetIds | Where-Object { $_ -le 0 }).Count -gt 0) { throw "Empty or invalid HRU domain" }
  if ($Expected -gt 0 -and $targetIds.Count -ne $Expected) { throw "Release count does not match HRU ID CSV" }
} else { $targetIds = @(1..$Expected) }
$target = @{}
foreach($id in $targetIds) { $target[[int]$id] = $true }
$Expected = $targetIds.Count
$seen = @{}
$missingRoots = @()
foreach($root in $Roots) {
  if (-not (Test-Path -LiteralPath $root)) {
    $missingRoots += $root
    continue
  }
  # Search read-only. The SWP output is conventionally run_XXXXX\swap.swp.
  Get-ChildItem -LiteralPath $root -Filter 'swap.swp' -File -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
    if ($_.Directory.Name -match '^run_(\d{1,5})$') {
      $hru = [int]$Matches[1]
      if ($target.ContainsKey($hru)) {
        $digest = (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash.ToLowerInvariant()
        if (-not $seen.ContainsKey($hru)) { $seen[$hru] = @() }
        $seen[$hru] += [pscustomobject]@{hru=$hru;path=$_.FullName;sha256=$digest;bytes=$_.Length}
      }
    }
  }
}
$rows = [System.Collections.Generic.List[object]]::new()
$conflicts = [System.Collections.Generic.List[object]]::new()
$missing = [System.Collections.Generic.List[int]]::new()
foreach($h in $targetIds) {
  if (-not $seen.ContainsKey($h)) { $missing.Add($h);continue }
  $distinct=@($seen[$h] | Select-Object -ExpandProperty sha256 -Unique)
  if($distinct.Count -ne 1) { $conflicts.Add([pscustomobject]@{hru=$h;copies=$seen[$h]});continue }
  $rows.Add($seen[$h][0])
}
$ok = $missing.Count -eq 0 -and $conflicts.Count -eq 0
$report = [ordered]@{
 schema_version=1;expected=$Expected;found_unique=$seen.Count;qualified_copies=$rows.Count;hru_ids_source=$HruIdsCsv
 missing_count=$missing.Count;missing_ids=@($missing);conflict_count=$conflicts.Count
 conflicts=@($conflicts);missing_roots=@($missingRoots)
 complete=$ok;production_admitted=$false;archive_created=$false
}
$reportPath = Join-Path $ReportDir 'swp_recovery_status.json'
if ($Package -and $ok) {
  Add-Type -AssemblyName System.IO.Compression
  $archive=Join-Path $ReportDir ('SWP_{0}_recovered.zip' -f $Expected)
  if (Test-Path -LiteralPath $archive) { throw "Archive already exists: $archive" }
  $zip = [System.IO.Compression.ZipFile]::Open($archive,[System.IO.Compression.ZipArchiveMode]::Create)
  try {
    foreach($record in $rows) {
      $entry=$zip.CreateEntry(('run_{0:D5}/swap.swp' -f [int]$record.hru),[System.IO.Compression.CompressionLevel]::Optimal)
      $read=[System.IO.File]::OpenRead($record.path)
      $write=$entry.Open()
      try { $read.CopyTo($write) } finally { $write.Dispose();$read.Dispose() }
    }
  } finally { $zip.Dispose() }
  $report.archive_created=$true
  $report.archive=$archive
  $report.archive_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $archive).Hash.ToLowerInvariant()
}
$rows | Export-Csv -NoTypeInformation -Encoding UTF8 -Path (Join-Path $ReportDir 'swp_files.csv')
$report | ConvertTo-Json -Depth 7 | Set-Content -Encoding UTF8 -Path $reportPath
Write-Host ("SWP found={0}/{1}, unresolved={2}, missing={3}" -f $seen.Count,$Expected,$conflicts.Count,$missing.Count)
Write-Host "Report: $reportPath"
if(-not $ok){exit 2}

exit 0
