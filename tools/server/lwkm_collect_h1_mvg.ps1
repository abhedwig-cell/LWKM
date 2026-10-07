#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ModelRoot,
    [Parameter(Mandatory=$true)][string]$OutputDir,
    [string]$BundleId = "LHM433_H1_MVG"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

function Sha256([string]$p) {
    (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()
}
function IsoUtc([datetime]$d) {
    $d.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffffffZ")
}
function WriteJson([string]$p, $o) {
    $o | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $p -Encoding UTF8
}

$model = (Get-Item -LiteralPath $ModelRoot -ErrorAction Stop).FullName.TrimEnd("\","/")
$out = [IO.Path]::GetFullPath($OutputDir).TrimEnd("\","/")
if ($out.StartsWith($model + "\", [StringComparison]::OrdinalIgnoreCase) -or $out.Equals($model, [StringComparison]::OrdinalIgnoreCase)) {
    throw "OutputDir must be outside ModelRoot"
}

$inputRoot = Join-Path $model "Data\2_Model_Input"
$h1 = Join-Path $inputRoot "modflow\riv\hoofdwater"
$mvg = Join-Path $inputRoot "modflow\drn"

if (-not (Test-Path -LiteralPath $h1 -PathType Container)) { throw "Missing H1 directory: $h1" }
if (-not (Test-Path -LiteralPath $mvg -PathType Container)) { throw "Missing MVG directory: $mvg" }

$bundle = Join-Path $out ($BundleId + "_Q2")
$manifestDir = Join-Path $bundle "00_manifest"
$h1Stage = Join-Path $bundle "10_H1"
$mvgStage = Join-Path $bundle "20_MVG"
$zip = Join-Path $out ($BundleId + "_Q4.zip")
$q4 = $zip + ".q4-verification.json"
$zipShaFile = $zip + ".sha256"

foreach ($p in @($bundle,$zip,$q4,$zipShaFile)) {
    if (Test-Path -LiteralPath $p) { throw "Output already exists: $p" }
}

New-Item -ItemType Directory -Path $manifestDir -Force | Out-Null
New-Item -ItemType Directory -Path $h1Stage -Force | Out-Null
New-Item -ItemType Directory -Path $mvgStage -Force | Out-Null

$spec = New-Object System.Collections.Generic.List[object]
$spec.Add([pscustomobject]@{logical_id="H1_CONDUCTANCE"; role="H1 layer-1 river conductance"; source=(Join-Path $h1 "COND_HL1_250.IDF"); rel="10_H1/COND_HL1_250.IDF"})
$spec.Add([pscustomobject]@{logical_id="H1_BOTTOM"; role="H1 river bottom"; source=(Join-Path $h1 "both.idf"); rel="10_H1/both.idf"})
$spec.Add([pscustomobject]@{logical_id="H1_INFILTRATION_FACTOR"; role="H1 layer-1 infiltration factor"; source=(Join-Path $h1 "infmz_h_250_l1.idf"); rel="10_H1/infmz_h_250_l1.idf"})

$peil = @(Get-ChildItem -LiteralPath $h1 -File -Force | Where-Object {$_.Name -like "peilh_*.idf"} | Sort-Object Name)
if ($peil.Count -eq 0) { throw "No peilh_*.idf files found in $h1" }
foreach ($f in $peil) {
    $spec.Add([pscustomobject]@{logical_id="H1_STAGE_DYNAMIC"; role="H1 dynamic stage"; source=$f.FullName; rel=("10_H1/" + $f.Name)})
}

$spec.Add([pscustomobject]@{logical_id="MVG_CONDUCTANCE"; role="MVG/surface-ditch conductance"; source=(Join-Path $mvg "COND_greppels.IDF"); rel="20_MVG/COND_greppels.IDF"})
$spec.Add([pscustomobject]@{logical_id="MVG_BOTTOM_STAGE"; role="MVG bottom and stage"; source=(Join-Path $mvg "BODH_BRP2012_MVGREP_250.IDF"); rel="20_MVG/BODH_BRP2012_MVGREP_250.IDF"})

$rows = New-Object System.Collections.Generic.List[object]

foreach ($s in $spec) {
    $src = Get-Item -LiteralPath $s.source -ErrorAction Stop
    $size0 = [int64]$src.Length
    $mtime0 = IsoUtc $src.LastWriteTimeUtc
    $hash0 = Sha256 $src.FullName
    $dst = Join-Path $bundle ($s.rel -replace "/", "\")
    New-Item -ItemType Directory -Path (Split-Path -Parent $dst) -Force | Out-Null
    Copy-Item -LiteralPath $src.FullName -Destination $dst -Force
    $dstHash = Sha256 $dst
    $dstSize = [int64](Get-Item -LiteralPath $dst).Length
    $src2 = Get-Item -LiteralPath $src.FullName
    $hash1 = Sha256 $src2.FullName

    if ($size0 -ne [int64]$src2.Length -or $mtime0 -ne (IsoUtc $src2.LastWriteTimeUtc) -or $hash0 -ne $hash1) {
        throw "Source changed during collection: $($src.FullName)"
    }
    if ($size0 -ne $dstSize -or $hash0 -ne $dstHash) {
        throw "Byte mismatch after copy: $($src.FullName)"
    }

    $rows.Add([pscustomobject]@{
        logical_id=$s.logical_id
        semantic_role=$s.role
        source_path=$src.FullName
        bundle_relative_path=$s.rel
        size_bytes=$size0
        source_last_write_utc=$mtime0
        sha256=$hash0
        qualification_status="PROVENANCE_BOUND_BYTE_IDENTICAL"
    })
}

$manifest = Join-Path $manifestDir "files.csv"
$rows | Export-Csv -LiteralPath $manifest -NoTypeInformation -Encoding UTF8
$manifestSha = Sha256 $manifest

$dates = @()
foreach ($f in $peil) {
    $m = [regex]::Match($f.Name, "(?i)^peilh_(\d{8})\.idf$")
    if ($m.Success) { $dates += $m.Groups[1].Value }
}
$dates = @($dates | Sort-Object)
$totalBytes = [int64](($rows | Measure-Object -Property size_bytes -Sum).Sum)

$collection = [ordered]@{
    schema_version=1
    status="H1_MVG_Q2_STAGED_BYTE_IDENTICAL"
    bundle_id=$BundleId
    model_root=$model
    model_input_root=$inputRoot
    source_authority="supplied LHM433 control INI"
    file_count=$rows.Count
    payload_bytes=$totalBytes
    h1_dynamic_stage_file_count=$peil.Count
    h1_dynamic_stage_date_min=if($dates.Count -gt 0){$dates[0]}else{""}
    h1_dynamic_stage_date_max=if($dates.Count -gt 0){$dates[-1]}else{""}
    manifest_sha256=$manifestSha
    collected_utc=(Get-Date).ToUniversalTime().ToString("o")
    collector_host=$env:COMPUTERNAME
    collector_user=$env:USERNAME
    powershell_version=$PSVersionTable.PSVersion.ToString()
    procedure="tools/server/lwkm_collect_h1_mvg.ps1"
}
WriteJson (Join-Path $manifestDir "collection.json") $collection

[System.IO.Compression.ZipFile]::CreateFromDirectory($bundle,$zip,[System.IO.Compression.CompressionLevel]::Optimal,$false)
$zipSha = Sha256 $zip
$zipSize = [int64](Get-Item -LiteralPath $zip).Length
("$zipSha  " + [IO.Path]::GetFileName($zip)) | Set-Content -LiteralPath $zipShaFile -Encoding ASCII

$verify = Join-Path $out ($BundleId + "_verify_" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $verify -Force | Out-Null
try {
    [System.IO.Compression.ZipFile]::ExtractToDirectory($zip,$verify)
    $vm = Import-Csv -LiteralPath (Join-Path $verify "00_manifest\files.csv")
    if ($vm.Count -ne $rows.Count) { throw "Extracted manifest count mismatch" }
    foreach ($r in $vm) {
        $p = Join-Path $verify ($r.bundle_relative_path -replace "/", "\")
        if (-not (Test-Path -LiteralPath $p -PathType Leaf)) { throw "Missing after extraction: $($r.bundle_relative_path)" }
        if ([int64](Get-Item -LiteralPath $p).Length -ne [int64]$r.size_bytes) { throw "Size mismatch after extraction: $($r.bundle_relative_path)" }
        if ((Sha256 $p) -ne $r.sha256) { throw "Hash mismatch after extraction: $($r.bundle_relative_path)" }
    }

    $result = [ordered]@{
        schema_version=1
        status="H1_MVG_Q4_IMMUTABLE_SNAPSHOT"
        bundle_id=$BundleId
        zip_path=$zip
        zip_size_bytes=$zipSize
        zip_sha256=$zipSha
        manifest_sha256=$manifestSha
        payload_file_count=$rows.Count
        payload_bytes=$totalBytes
        h1_dynamic_stage_file_count=$peil.Count
        h1_dynamic_stage_date_min=if($dates.Count -gt 0){$dates[0]}else{""}
        h1_dynamic_stage_date_max=if($dates.Count -gt 0){$dates[-1]}else{""}
        zero_unexplained_file_identity_differences=$true
        verified_utc=(Get-Date).ToUniversalTime().ToString("o")
    }
    WriteJson $q4 $result
    $result | ConvertTo-Json -Depth 20
}
finally {
    if (Test-Path -LiteralPath $verify) { Remove-Item -LiteralPath $verify -Recurse -Force }
}
