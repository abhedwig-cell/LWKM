#requires -Version 5.1
<#
Inventory LHM control INI files for LWKM provenance.

This parser is intentionally conservative:
- it never edits the INI files;
- it records every non-comment assignment;
- it resolves ConfigObj-style interpolation tokens such as %(%model%)s;
- it emits path-like candidates without assuming that a current file is the
  historical byte-identical file;
- it records SHA-256 for each supplied INI when raw bytes are available.

Outputs:
  ini-manifest.csv
  ini-assignments.csv
  ini-path-candidates.csv
  ini-summary.json
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string[]]$IniPath,

    [Parameter(Mandatory=$true)]
    [string]$OutputDir
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-UtcIso([datetime]$Value) {
    return $Value.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffffffZ")
}

function Write-JsonFile([string]$Path, $Object) {
    $Object | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Resolve-InterpolatedValue([string]$Value, [hashtable]$Map) {
    $resolved = $Value
    for ($iteration = 0; $iteration -lt 30; $iteration++) {
        $match = [regex]::Match($resolved, '%\(([^)]+)\)s')
        if (-not $match.Success) { break }
        $key = $match.Groups[1].Value
        if (-not $Map.ContainsKey($key)) { break }
        $replacement = [string]$Map[$key]
        $resolved = $resolved.Substring(0, $match.Index) +
                    $replacement +
                    $resolved.Substring($match.Index + $match.Length)
    }
    return $resolved
}

function Get-SectionPath([string[]]$Sections) {
    return (($Sections | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }) -join "/")
}

function Test-PathLike([string]$Value) {
    if ([string]::IsNullOrWhiteSpace($Value)) { return $false }
    $v = $Value.Trim().Trim("'").Trim('"')
    if ($v -match '^[A-Za-z]:\\') { return $true }
    if ($v -match '^\\\\') { return $true }
    if ($v -match '[\\/]' -and $v -match '(\.[A-Za-z0-9]{1,8}|\*|\?|\\$|/$)') { return $true }
    return $false
}

function Get-PathKind([string]$Value) {
    $v = $Value.Trim().Trim("'").Trim('"')
    if ($v -match '%\([^)]+\)s') { return "UNRESOLVED_INTERPOLATION" }
    if ($v -match '^[A-Za-z]:\\') { return "ABSOLUTE_DRIVE" }
    if ($v -match '^\\\\') { return "UNC" }
    if ($v -match '[\\/]') { return "RELATIVE_OR_PATTERN" }
    return "NOT_PATH"
}

function Get-ProvenanceRole([string]$SectionPath) {
    if ($SectionPath -match '(^|/)DATA(/|$)') { return "LHM_INPUT_OR_RESOURCE_DECLARATION" }
    if ($SectionPath -match '(^|/)RESTART(/|$)') { return "LHM_RESTART_DECLARATION" }
    if ($SectionPath -match '(^|/)EXE(/|$)') { return "EXECUTABLE_BINDING" }
    return "CONFIG_REFERENCE"
}

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
$OutputDir = [IO.Path]::GetFullPath($OutputDir)

$manifestRows = New-Object System.Collections.Generic.List[object]
$assignmentRows = New-Object System.Collections.Generic.List[object]
$pathRows = New-Object System.Collections.Generic.List[object]

foreach ($rawIni in $IniPath) {
    $ini = Get-Item -LiteralPath $rawIni -ErrorAction Stop
    if ($ini.PSIsContainer) { throw "INI path is a directory: $rawIni" }

    $manifestRows.Add([pscustomobject]@{
        ini_name = $ini.Name
        ini_path = $ini.FullName
        size_bytes = $ini.Length
        sha256 = (Get-FileHash -LiteralPath $ini.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        last_write_utc = Get-UtcIso $ini.LastWriteTimeUtc
    })

    $lines = Get-Content -LiteralPath $ini.FullName
    $sections = @("", "", "", "", "")
    $assignments = New-Object System.Collections.Generic.List[object]
    $valueMap = @{}

    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = [string]$lines[$i]
        $trim = $line.Trim()
        if ([string]::IsNullOrWhiteSpace($trim)) { continue }
        if ($trim.StartsWith("#") -or $trim.StartsWith(";")) { continue }

        $sectionMatch = [regex]::Match($trim, '^(\[{1,4})([^\]]+)(\]{1,4})\s*(?:#.*)?$')
        if ($sectionMatch.Success) {
            $depth = $sectionMatch.Groups[1].Value.Length
            $name = $sectionMatch.Groups[2].Value.Trim()
            if ($depth -ge $sections.Count) { throw "Unsupported section depth $depth at $($ini.Name):$($i+1)" }
            $sections[$depth] = $name
            for ($d = $depth + 1; $d -lt $sections.Count; $d++) { $sections[$d] = "" }
            continue
        }

        $assignmentMatch = [regex]::Match($line, '^\s*([^#;][^=]*?)\s*=\s*(.*?)\s*(?:#.*)?$')
        if (-not $assignmentMatch.Success) { continue }

        $key = $assignmentMatch.Groups[1].Value.Trim()
        $rawValue = $assignmentMatch.Groups[2].Value.Trim()
        $sectionPath = Get-SectionPath $sections
        $assignments.Add([pscustomobject]@{
            ini_name = $ini.Name
            ini_path = $ini.FullName
            line_number = $i + 1
            section_path = $sectionPath
            key = $key
            raw_value = $rawValue
        })

        # Preserve latest declaration for interpolation. Config files may reuse
        # ordinary keys in later sections; interpolation variables are normally
        # the %-wrapped DATA aliases and remain explicit in the output table.
        $valueMap[$key] = $rawValue
    }

    # Resolve recursively against the complete assignment map.
    $resolvedMap = @{}
    foreach ($entry in $assignments) {
        $resolved = Resolve-InterpolatedValue $entry.raw_value $valueMap
        # A second pass can resolve nested aliases after the first substitution.
        for ($j = 0; $j -lt 10; $j++) {
            $next = Resolve-InterpolatedValue $resolved $valueMap
            if ($next -eq $resolved) { break }
            $resolved = $next
        }
        $resolvedMap["$($entry.section_path)|$($entry.key)|$($entry.line_number)"] = $resolved
    }

    foreach ($entry in $assignments) {
        $mapKey = "$($entry.section_path)|$($entry.key)|$($entry.line_number)"
        $resolved = [string]$resolvedMap[$mapKey]
        $assignmentRows.Add([pscustomobject]@{
            ini_name = $entry.ini_name
            ini_path = $entry.ini_path
            line_number = $entry.line_number
            section_path = $entry.section_path
            key = $entry.key
            raw_value = $entry.raw_value
            resolved_value = $resolved
        })

        if (Test-PathLike $resolved) {
            $clean = $resolved.Trim().Trim("'").Trim('"')
            $kind = Get-PathKind $clean
            $exists = ""
            $resolvedCount = ""
            if ($kind -in @("ABSOLUTE_DRIVE","UNC")) {
                try {
                    $resolvedItems = @(Get-ChildItem -Path $clean -File -ErrorAction SilentlyContinue)
                    if ($resolvedItems.Count -eq 0 -and (Test-Path -LiteralPath $clean -PathType Leaf)) {
                        $resolvedItems = @(Get-Item -LiteralPath $clean)
                    }
                    $resolvedCount = $resolvedItems.Count
                    $exists = ($resolvedItems.Count -gt 0).ToString().ToLowerInvariant()
                }
                catch {
                    $exists = "false"
                    $resolvedCount = 0
                }
            }

            $pathRows.Add([pscustomobject]@{
                ini_name = $entry.ini_name
                line_number = $entry.line_number
                section_path = $entry.section_path
                key = $entry.key
                raw_value = $entry.raw_value
                resolved_value = $clean
                path_kind = $kind
                provenance_role = Get-ProvenanceRole $entry.section_path
                current_path_exists = $exists
                current_match_count = $resolvedCount
                qualification_status = "INI_DECLARED_NOT_FILE_QUALIFIED"
            })
        }
    }
}

$manifestPath = Join-Path $OutputDir "ini-manifest.csv"
$assignmentsPath = Join-Path $OutputDir "ini-assignments.csv"
$pathsPath = Join-Path $OutputDir "ini-path-candidates.csv"
$summaryPath = Join-Path $OutputDir "ini-summary.json"

$manifestRows | Export-Csv -LiteralPath $manifestPath -NoTypeInformation -Encoding UTF8
$assignmentRows | Export-Csv -LiteralPath $assignmentsPath -NoTypeInformation -Encoding UTF8
$pathRows | Export-Csv -LiteralPath $pathsPath -NoTypeInformation -Encoding UTF8

$summary = [ordered]@{
    schema_version = 1
    status = "INI_PROVENANCE_INVENTORY_CREATED"
    ini_count = $manifestRows.Count
    assignment_count = $assignmentRows.Count
    path_candidate_count = $pathRows.Count
    created_utc = (Get-Date).ToUniversalTime().ToString("o")
    outputs = [ordered]@{
        manifest = $manifestPath
        assignments = $assignmentsPath
        paths = $pathsPath
    }
    caveat = "An INI path declaration proves configuration intent. It does not by itself prove that a currently resolved file is the historical byte-identical input."
}
Write-JsonFile $summaryPath $summary
$summary | ConvertTo-Json -Depth 10
