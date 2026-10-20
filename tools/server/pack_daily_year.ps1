param([Parameter(Mandatory=$true)][string]$Directory,
      [Parameter(Mandatory=$true)][int]$Year,
      [string]$Output)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$root = (Resolve-Path $Directory).Path
$config = Get-Content -LiteralPath (Join-Path $root 'transfer.json') -Raw | ConvertFrom-Json
$rows = @($config.files | Where-Object { $_.date.StartsWith("$Year-") })
if ($rows.Count -eq 0) { throw 'No configured days in selected year' }
$config.start = ($rows | Sort-Object date | Select-Object -First 1).date
$config.end = ($rows | Sort-Object date | Select-Object -Last 1).date
$config.files = $rows
if (-not $Output) { $Output = Join-Path $root ("transfer_$Year.zip") }
$temporary = "$Output.partial"
Remove-Item -LiteralPath $temporary -ErrorAction SilentlyContinue
$stream = [System.IO.File]::Open($temporary, [System.IO.FileMode]::CreateNew)
$zip = New-Object System.IO.Compression.ZipArchive($stream, [System.IO.Compression.ZipArchiveMode]::Create)
try {
    $entries = @($rows | ForEach-Object { @{path=$_.path; sha256=$_.sha256} })
    $entries += @{path=$config.source_manifest_path; sha256=$config.source_manifest_sha256}
    foreach ($item in $entries) {
        $name = [string]$item.path
        if ([System.IO.Path]::IsPathRooted($name) -or $name.Contains('..') -or $name.Contains(':') -or $name.Contains('\')) { throw 'Unsafe transfer path' }
        $path = Join-Path $root $name
        if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower() -ne $item.sha256) { throw "SHA256 mismatch: $name" }
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip,$path,$name,[System.IO.Compression.CompressionLevel]::Optimal) | Out-Null
    }
    $entry = $zip.CreateEntry('transfer.json')
    $writer = New-Object System.IO.StreamWriter($entry.Open(), (New-Object System.Text.UTF8Encoding($false)))
    try { $writer.Write(($config | ConvertTo-Json -Depth 60)) } finally { $writer.Dispose() }
} finally { $zip.Dispose(); $stream.Dispose() }
Move-Item -LiteralPath $temporary -Destination $Output -Force
Get-FileHash -LiteralPath $Output -Algorithm SHA256
