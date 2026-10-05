#requires -Version 5.1
<#
LWKM W01 provenance freeze bootstrap for Windows PowerShell.

Current implemented gates:
  q0 - capture named source roots and run identity
  q1 - inventory the versioned source specification without copying source data

This script intentionally does NOT copy, modify or archive source data in q0/q1.
It is the no-Python bootstrap path for the LHM server.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("q0","q1")]
    [string]$Command,

    [string[]]$Root,
    [string]$OutputRoot,
    [string]$RunId,
    [string]$ModelVersion = "",
    [string]$SimulationStart = "",
    [string]$SimulationEnd = "",
    [switch]$CompletedRun,
    [string]$RestartHistory = "",
    [string]$Notes = "",
    [switch]$Force,

    [string]$Q0Path,
    [string]$SpecPath,
    [string]$OutputDir
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-UtcIso([datetime]$Value) {
    return $Value.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffffffZ")
}

function Write-JsonFile([string]$Path, $Object) {
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    $Object | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Normalize-Hint([string]$Text) {
    if ([string]::IsNullOrWhiteSpace($Text)) { return "" }
    return ($Text -replace "\\","/").Trim("/").ToLowerInvariant()
}

function Parse-Bool([string]$Text) {
    if ($null -eq $Text) { return $false }
    return @("1","true","yes","y") -contains $Text.Trim().ToLowerInvariant()
}

function Invoke-Q0 {
    if (-not $Root -or $Root.Count -lt 1) {
        throw "q0 requires at least one -Root 'KEY=PATH'"
    }
    if ([string]::IsNullOrWhiteSpace($OutputRoot)) { throw "q0 requires -OutputRoot" }
    if ([string]::IsNullOrWhiteSpace($RunId)) { throw "q0 requires -RunId" }

    $roots = [ordered]@{}
    foreach ($raw in $Root) {
        $ix = $raw.IndexOf("=")
        if ($ix -lt 1) { throw "Root must be KEY=PATH, got: $raw" }
        $key = $raw.Substring(0,$ix).Trim().ToUpperInvariant()
        $value = $raw.Substring($ix+1).Trim()
        if ($roots.Contains($key)) { throw "Duplicate root key: $key" }

        $item = Get-Item -LiteralPath $value -ErrorAction Stop
        if (-not $item.PSIsContainer) { throw "Root $key is not a directory: $value" }
        $roots[$key] = [ordered]@{
            path = $item.FullName
            last_write_utc = Get-UtcIso $item.LastWriteTimeUtc
        }
    }

    $manifestDir = Join-Path (Join-Path ([IO.Path]::GetFullPath($OutputRoot)) $RunId) "00_manifest"
    New-Item -ItemType Directory -Path $manifestDir -Force | Out-Null
    $q0 = Join-Path $manifestDir "q0-run.json"
    if ((Test-Path -LiteralPath $q0) -and -not $Force) {
        throw "Q0 record already exists: $q0. Use -Force only for intentional replacement."
    }

    $obj = [ordered]@{
        schema_version = 1
        gate = "Q0"
        status = "Q0_RUN_IDENTITY_CAPTURED_NOT_YET_ADMITTED"
        run_id = $RunId
        server_hostname = $env:COMPUTERNAME
        roots = $roots
        model_version = $ModelVersion
        simulation_start = $SimulationStart
        simulation_end = $SimulationEnd
        completed_run_assertion = [bool]$CompletedRun
        restart_history = $RestartHistory
        notes = $Notes
        collection_operator = $env:USERNAME
        powershell_version = $PSVersionTable.PSVersion.ToString()
        captured_utc = (Get-Date).ToUniversalTime().ToString("o")
        procedure = "tools/server/lwkm_w01.ps1"
    }

    Write-JsonFile $q0 $obj

    [ordered]@{
        gate = "Q0"
        status = $obj.status
        q0 = $q0
        roots = $roots
    } | ConvertTo-Json -Depth 10
}

function Invoke-Q1 {
    if ([string]::IsNullOrWhiteSpace($Q0Path)) { throw "q1 requires -Q0Path" }
    if ([string]::IsNullOrWhiteSpace($SpecPath)) { throw "q1 requires -SpecPath" }
    if ([string]::IsNullOrWhiteSpace($OutputDir)) { throw "q1 requires -OutputDir" }

    $q0 = Get-Content -LiteralPath $Q0Path -Raw | ConvertFrom-Json
    $spec = Import-Csv -LiteralPath $SpecPath
    if (-not $spec -or $spec.Count -eq 0) { throw "Source specification is empty" }

    $requiredColumns = @(
        "logical_id","root_key","provenance_class","required_by",
        "filename_pattern","path_hint","required","max_matches",
        "temporal_scope","expected_format","semantic_role"
    )
    foreach ($col in $requiredColumns) {
        if (-not ($spec[0].PSObject.Properties.Name -contains $col)) {
            throw "Source specification missing column: $col"
        }
    }

    $roots = @{}
    foreach ($prop in $q0.roots.PSObject.Properties) {
        $key = $prop.Name.ToUpperInvariant()
        $path = $prop.Value.path
        $item = Get-Item -LiteralPath $path -ErrorAction Stop
        if (-not $item.PSIsContainer) { throw "Q0 root $key is unavailable: $path" }
        $roots[$key] = $item.FullName
    }
    if ($roots.Count -eq 0) { throw "Q0 contains no roots" }

    $seenIds = @{}
    foreach ($row in $spec) {
        $id = $row.logical_id.Trim()
        if ([string]::IsNullOrWhiteSpace($id)) { throw "Empty logical_id in source specification" }
        if ($seenIds.ContainsKey($id)) { throw "Duplicate logical_id: $id" }
        $seenIds[$id] = $true

        $rootKey = $row.root_key.Trim().ToUpperInvariant()
        if (-not $roots.ContainsKey($rootKey)) {
            throw "Source spec references undefined Q0 root key '$rootKey' for $id"
        }
        if (-not @("A","B","C","D").Contains($row.provenance_class.Trim())) {
            throw "Unknown provenance_class for $id"
        }
    }

    $indexes = @{}
    $indexedCount = 0
    foreach ($key in $roots.Keys) {
        $rootPath = $roots[$key]
        $files = Get-ChildItem -LiteralPath $rootPath -File -Recurse -Force -ErrorAction SilentlyContinue |
            Where-Object {
                $_.FullName -notmatch '\\.git\\' -and
                $_.FullName -notmatch '\\System Volume Information\\' -and
                $_.FullName -notmatch '\\$RECYCLE\.BIN\\'
            }
        $indexedCount += @($files).Count
        $indexes[$key] = @($files)
    }

    $inventory = New-Object System.Collections.Generic.List[object]
    $items = New-Object System.Collections.Generic.List[object]
    $missing = New-Object System.Collections.Generic.List[string]
    $ambiguous = New-Object System.Collections.Generic.List[string]

    foreach ($row in $spec) {
        $id = $row.logical_id.Trim()
        $rootKey = $row.root_key.Trim().ToUpperInvariant()
        $rootPath = $roots[$rootKey]
        $pattern = $row.filename_pattern.Trim()
        $hint = Normalize-Hint $row.path_hint
        $required = Parse-Bool $row.required
        $maxMatches = $null
        if (-not [string]::IsNullOrWhiteSpace($row.max_matches)) {
            $maxMatches = [int]$row.max_matches
        }

        $matches = @(
            $indexes[$rootKey] | Where-Object {
                if (-not ($_.Name -like $pattern)) { return $false }
                if ([string]::IsNullOrWhiteSpace($hint)) { return $true }
                $rel = $_.FullName.Substring($rootPath.Length).TrimStart("\","/") -replace "\\","/"
                return $rel.ToLowerInvariant().Contains($hint)
            } | Sort-Object FullName
        )

        if ($required -and $matches.Count -eq 0) {
            $status = "MISSING_REQUIRED"
            $missing.Add($id)
        }
        elseif ($matches.Count -eq 0) {
            $status = "OPTIONAL_NOT_FOUND"
        }
        elseif ($null -ne $maxMatches -and $matches.Count -gt $maxMatches) {
            $status = "AMBIGUOUS_TOO_MANY_MATCHES"
            $ambiguous.Add($id)
        }
        else {
            $status = "RESOLVED"
        }

        $selected = ($status -eq "RESOLVED")
        $items.Add([pscustomobject]@{
            logical_id = $id
            root_key = $rootKey
            status = $status
            match_count = $matches.Count
            required = $required
            max_matches = $maxMatches
        })

        foreach ($m in $matches) {
            $rel = $m.FullName.Substring($rootPath.Length).TrimStart("\","/") -replace "\\","/"
            $inventory.Add([pscustomobject]@{
                logical_id = $id
                source_root_key = $rootKey
                provenance_class = $row.provenance_class.Trim()
                required_by = $row.required_by.Trim()
                semantic_role = $row.semantic_role.Trim()
                expected_format = $row.expected_format.Trim()
                temporal_scope = $row.temporal_scope.Trim()
                source_path = $m.FullName
                source_relative_path = $rel
                size_bytes = $m.Length
                last_write_utc = Get-UtcIso $m.LastWriteTimeUtc
                selected = $selected.ToString().ToLowerInvariant()
                q1_item_status = $status
                qualification_status = "RECOVERED_UNQUALIFIED"
            })
        }
    }

    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    $inventoryPath = Join-Path $OutputDir "q1-inventory.csv"
    $summaryPath = Join-Path $OutputDir "q1-summary.json"
    $specCopy = Join-Path $OutputDir ([IO.Path]::GetFileName($SpecPath))

    $inventory | Export-Csv -LiteralPath $inventoryPath -NoTypeInformation -Encoding UTF8
    Copy-Item -LiteralPath $SpecPath -Destination $specCopy -Force

    $overall = if ($missing.Count -eq 0 -and $ambiguous.Count -eq 0) { "Q1_PASS" } else { "Q1_FAIL" }

    $summary = [ordered]@{
        schema_version = 1
        gate = "Q1"
        status = $overall
        run_id = $q0.run_id
        roots = $q0.roots
        source_spec = ([IO.Path]::GetFullPath($SpecPath))
        source_spec_sha256 = Get-Sha256 $SpecPath
        inventory_file = ([IO.Path]::GetFullPath($inventoryPath))
        inventory_sha256 = Get-Sha256 $inventoryPath
        indexed_file_count = $indexedCount
        matched_file_rows = $inventory.Count
        missing_required = @($missing)
        ambiguous = @($ambiguous)
        items = @($items)
        captured_utc = (Get-Date).ToUniversalTime().ToString("o")
    }
    Write-JsonFile $summaryPath $summary

    [ordered]@{
        gate = "Q1"
        status = $overall
        inventory = $inventoryPath
        missing_required = @($missing)
        ambiguous = @($ambiguous)
    } | ConvertTo-Json -Depth 10

    if ($overall -eq "Q1_PASS") { return 0 } else { return 2 }
}

try {
    switch ($Command) {
        "q0" { exit (Invoke-Q0) }
        "q1" { exit (Invoke-Q1) }
    }
}
catch {
    [ordered]@{
        status = "FAIL_CLOSED"
        command = $Command
        error_type = $_.Exception.GetType().Name
        error = $_.Exception.Message
    } | ConvertTo-Json -Depth 10 | Write-Error
    exit 10
}
