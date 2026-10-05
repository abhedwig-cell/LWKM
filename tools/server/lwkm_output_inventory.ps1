#requires -Version 5.1
<#
Inventory the authoritative Deltares-collected LHM output tree for LWKM.

Read-only. No source files are modified or copied.

Outputs:
  output-inventory.csv
  output-folder-summary.csv
  output-summary.json

Hashing every file is deliberately NOT done at this discovery stage. File hashes
are required later for the subset actually consumed by the qualified LWKM chain
(or for a full immutable snapshot if that storage policy is chosen).
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$Root,

    [Parameter(Mandatory=$true)]
    [string]$OutputDir
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-JsonFile([string]$Path, $Object) {
    $Object | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $Path -Encoding UTF8
}

$rootItem = Get-Item -LiteralPath $Root -ErrorAction Stop
if (-not $rootItem.PSIsContainer) { throw "Root is not a directory: $Root" }
$rootFull = $rootItem.FullName.TrimEnd("\","/")

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
$OutputDir = [IO.Path]::GetFullPath($OutputDir)

$rows = New-Object System.Collections.Generic.List[object]

Get-ChildItem -LiteralPath $rootFull -File -Recurse -Force -ErrorAction SilentlyContinue |
    ForEach-Object {
        $rel = $_.FullName.Substring($rootFull.Length).TrimStart("\","/")
        $parts = $rel -split '\\'
        $top = if ($parts.Count -gt 1) { $parts[0] } else { "." }
        $second = if ($parts.Count -gt 2) { $parts[1] } else { "" }

        $yearMatch = [regex]::Match($_.Name, '(19[0-9]{2}|20[0-9]{2})')
        $year = if ($yearMatch.Success) { $yearMatch.Value } else { "" }

        $rows.Add([pscustomobject]@{
            relative_path = $rel
            top_folder = $top
            second_folder = $second
            name = $_.Name
            extension = $_.Extension.ToLowerInvariant()
            size_bytes = $_.Length
            last_write_utc = $_.LastWriteTimeUtc.ToString("o")
            filename_year = $year
            qualification_status = "DISCOVERED_UNQUALIFIED"
        })
    }

$inventoryPath = Join-Path $OutputDir "output-inventory.csv"
$rows | Sort-Object relative_path | Export-Csv -LiteralPath $inventoryPath -NoTypeInformation -Encoding UTF8

$folderSummary = @(
    $rows | Group-Object top_folder | ForEach-Object {
        $total = ($_.Group | Measure-Object -Property size_bytes -Sum).Sum
        [pscustomobject]@{
            top_folder = $_.Name
            file_count = $_.Count
            total_bytes = [int64]$total
            min_year = (@($_.Group.filename_year | Where-Object { $_ }) | Sort-Object | Select-Object -First 1)
            max_year = (@($_.Group.filename_year | Where-Object { $_ }) | Sort-Object | Select-Object -Last 1)
        }
    } | Sort-Object top_folder
)
$folderSummaryPath = Join-Path $OutputDir "output-folder-summary.csv"
$folderSummary | Export-Csv -LiteralPath $folderSummaryPath -NoTypeInformation -Encoding UTF8

$totalBytes = ($rows | Measure-Object -Property size_bytes -Sum).Sum
$extensions = @(
    $rows | Group-Object extension | Sort-Object Count -Descending | ForEach-Object {
        [ordered]@{ extension = $_.Name; count = $_.Count }
    }
)

$summary = [ordered]@{
    schema_version = 1
    status = "W01_OUTPUT_AUTHORITY_INVENTORIED_NOT_QUALIFIED"
    authority_root = $rootFull
    file_count = $rows.Count
    total_bytes = [int64]$totalBytes
    top_folder_count = $folderSummary.Count
    extensions = $extensions
    created_utc = (Get-Date).ToUniversalTime().ToString("o")
    outputs = [ordered]@{
        inventory = $inventoryPath
        folder_summary = $folderSummaryPath
    }
    caveat = "Discovery only. Files actually consumed downstream still require SHA-256, semantic qualification and consumer binding."
}
$summaryPath = Join-Path $OutputDir "output-summary.json"
Write-JsonFile $summaryPath $summary
$summary | ConvertTo-Json -Depth 10
