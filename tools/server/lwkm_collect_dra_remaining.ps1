#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ModelRoot,
    [Parameter(Mandatory=$true)][string]$OutputDir,
    [string]$BundleId = "LHM433_DRA_REMAINING"
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
    $o | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $p -Encoding UTF8
}

$model = (Get-Item -LiteralPath $ModelRoot -ErrorAction Stop).FullName.TrimEnd("\","/")
$out = [IO.Path]::GetFullPath($OutputDir).TrimEnd("\","/")
if ($out.StartsWith($model + "\", [StringComparison]::OrdinalIgnoreCase) -or $out.Equals($model, [StringComparison]::OrdinalIgnoreCase)) {
    throw "OutputDir must be outside ModelRoot"
}

$inputRoot = Join-Path $model "Data\2_Model_Input"
$riv = Join-Path $inputRoot "modflow\riv\regionaal"
$drn = Join-Path $inputRoot "modflow\drn"
$msgrid = Join-Path $inputRoot "metaswap\grid"

foreach ($d in @($riv,$drn,$msgrid)) {
    if (-not (Test-Path -LiteralPath $d -PathType Container)) { throw "Missing source directory: $d" }
}

$bundle = Join-Path $out ($BundleId + "_Q2")
$manifestDir = Join-Path $bundle "00_manifest"
$zip = Join-Path $out ($BundleId + "_Q4.zip")
$q4 = $zip + ".q4-verification.json"
$zipShaFile = $zip + ".sha256"
foreach ($p in @($bundle,$zip,$q4,$zipShaFile)) {
    if (Test-Path -LiteralPath $p) { throw "Output already exists: $p" }
}
New-Item -ItemType Directory -Path $manifestDir -Force | Out-Null

$spec = New-Object System.Collections.Generic.List[object]
function AddSpec([string]$id,[string]$role,[string]$source,[string]$rel,[string]$authority) {
    $script:spec.Add([pscustomobject]@{logical_id=$id; semantic_role=$role; source=$source; rel=$rel; authority=$authority})
}

# P/S/T source set used by the current HRU DRA control.
AddSpec "P_CONDUCTANCE" "Primary river conductance" (Join-Path $riv "COND_primair.IDF") "10_RIV/P/COND_primair.IDF" "CURRENT_HRU_DRA_CONTROL"
AddSpec "S_CONDUCTANCE" "Secondary river conductance" (Join-Path $riv "COND_secundair.IDF") "10_RIV/S/COND_secundair.IDF" "CURRENT_HRU_DRA_CONTROL"
AddSpec "T_CONDUCTANCE" "Tertiary river conductance" (Join-Path $riv "COND_tertiair.IDF") "10_RIV/T/COND_tertiair.IDF" "CURRENT_HRU_DRA_CONTROL"
AddSpec "P_INFILTRATION_FACTOR" "Primary river infiltration factor" (Join-Path $riv "inf_mz_primair.IDF") "10_RIV/P/inf_mz_primair.IDF" "CURRENT_HRU_DRA_CONTROL_AND_LHM_INI"
AddSpec "S_INFILTRATION_FACTOR" "Secondary river infiltration factor" (Join-Path $riv "inf_mz_secundair.IDF") "10_RIV/S/inf_mz_secundair.IDF" "CURRENT_HRU_DRA_CONTROL_AND_LHM_INI"
AddSpec "T_INFILTRATION_FACTOR" "Tertiary river infiltration factor" (Join-Path $riv "inf_mz_tertiair.IDF") "10_RIV/T/inf_mz_tertiair.IDF" "CURRENT_HRU_DRA_CONTROL_AND_LHM_INI"
AddSpec "P_BOTTOM_HRU" "Primary bottom used by current HRU DRA control" (Join-Path $riv "steady-state\BODH_P1J_250.IDF") "10_RIV/P/BODH_P1J_250.IDF" "CURRENT_HRU_DRA_CONTROL"
AddSpec "S_BOTTOM_HRU" "Secondary bottom used by current HRU DRA control" (Join-Path $riv "steady-state\BODH_S1J_250.IDF") "10_RIV/S/BODH_S1J_250.IDF" "CURRENT_HRU_DRA_CONTROL"
AddSpec "T_BOTTOM_HRU" "Tertiary bottom used by current HRU DRA control" (Join-Path $riv "steady-state\BODH_T1J_250.IDF") "10_RIV/T/BODH_T1J_250.IDF" "CURRENT_HRU_DRA_CONTROL"
AddSpec "P_LEVEL_SUM" "Primary summer level" (Join-Path $riv "PEIL_P1Z_250.IDF") "10_RIV/P/PEIL_P1Z_250.IDF" "CURRENT_HRU_DRA_CONTROL_AND_LHM_INI"
AddSpec "P_LEVEL_WIN" "Primary winter level" (Join-Path $riv "PEIL_P1W_250.IDF") "10_RIV/P/PEIL_P1W_250.IDF" "CURRENT_HRU_DRA_CONTROL_AND_LHM_INI"
AddSpec "S_LEVEL_SUM" "Secondary summer level" (Join-Path $riv "PEIL_S1Z_250.IDF") "10_RIV/S/PEIL_S1Z_250.IDF" "CURRENT_HRU_DRA_CONTROL_AND_LHM_INI"
AddSpec "S_LEVEL_WIN" "Secondary winter level" (Join-Path $riv "PEIL_S1W_250.IDF") "10_RIV/S/PEIL_S1W_250.IDF" "CURRENT_HRU_DRA_CONTROL_AND_LHM_INI"
AddSpec "T_LEVEL_SUM" "Tertiary summer level" (Join-Path $riv "PEIL_T1Z_250.IDF") "10_RIV/T/PEIL_T1Z_250.IDF" "CURRENT_HRU_DRA_CONTROL_AND_LHM_INI"
AddSpec "T_LEVEL_WIN" "Tertiary winter level" (Join-Path $riv "PEIL_T1W_250.IDF") "10_RIV/T/PEIL_T1W_250.IDF" "CURRENT_HRU_DRA_CONTROL_AND_LHM_INI"

# Package-bottom candidates from the LHM INI are retained separately for comparison.
AddSpec "P_BOTTOM_LHM_SUM" "Primary LHM-package summer river bottom" (Join-Path $riv "BODH_P1Z_250.IDF") "15_LHM_BOTTOM_COMPARISON/P/BODH_P1Z_250.IDF" "LHM_INI_PACKAGE"
AddSpec "P_BOTTOM_LHM_WIN" "Primary LHM-package winter river bottom" (Join-Path $riv "BODH_P1W_250.IDF") "15_LHM_BOTTOM_COMPARISON/P/BODH_P1W_250.IDF" "LHM_INI_PACKAGE"
AddSpec "S_BOTTOM_LHM_SUM" "Secondary LHM-package summer river bottom" (Join-Path $riv "BODH_S1Z_250.IDF") "15_LHM_BOTTOM_COMPARISON/S/BODH_S1Z_250.IDF" "LHM_INI_PACKAGE"
AddSpec "S_BOTTOM_LHM_WIN" "Secondary LHM-package winter river bottom" (Join-Path $riv "BODH_S1W_250.IDF") "15_LHM_BOTTOM_COMPARISON/S/BODH_S1W_250.IDF" "LHM_INI_PACKAGE"

# Pipe drainage and overland-flow sources.
AddSpec "PIPE_CONDUCTANCE" "Pipe-drainage conductance" (Join-Path $drn "COND_buisdrainage.IDF") "20_DRN/PIPE/COND_buisdrainage.IDF" "CURRENT_HRU_DRA_CONTROL_AND_LHM_INI"
AddSpec "PIPE_BOTTOM_STAGE" "Pipe-drainage bottom/stage" (Join-Path $drn "BODH_B_250.IDF") "20_DRN/PIPE/BODH_B_250.IDF" "CURRENT_HRU_DRA_CONTROL_AND_LHM_INI"
AddSpec "OLF_CONDUCTANCE" "Overland-flow conductance" (Join-Path $drn "COND_SOF_250.IDF") "20_DRN/OLF/COND_SOF_250.IDF" "CURRENT_HRU_DRA_CONTROL_AND_LHM_INI"
AddSpec "OLF_BOTTOM_STAGE" "Overland-flow bottom/stage" (Join-Path $drn "BODH_SOF_250.IDF") "20_DRN/OLF/BODH_SOF_250.IDF" "CURRENT_HRU_DRA_CONTROL_AND_LHM_INI"

# Authoritative LHM ground-level source; modern tooling converts cm to m explicitly.
AddSpec "AHN_GROUND_CM" "LHM MetaSWAP ground level in centimetres" (Join-Path $msgrid "ahn_f250_cm.asc") "30_GROUND/ahn_f250_cm.asc" "LHM_INI_MODEL_INPUT"

$rows = New-Object System.Collections.Generic.List[object]
foreach ($s in $spec) {
    $src = Get-Item -LiteralPath $s.source -ErrorAction Stop
    if ($src.PSIsContainer) { throw "Expected file, found directory: $($s.source)" }
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
        semantic_role=$s.semantic_role
        source_authority=$s.authority
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
$totalBytes = [int64](($rows | Measure-Object -Property size_bytes -Sum).Sum)
$collection = [ordered]@{
    schema_version=1
    status="DRA_REMAINING_Q2_STAGED_BYTE_IDENTICAL"
    bundle_id=$BundleId
    model_root=$model
    model_input_root=$inputRoot
    file_count=$rows.Count
    payload_bytes=$totalBytes
    required_physical_systems=@("RIV_PRIMARY","RIV_SECONDARY","RIV_TERTIARY","DRN_PIPE","DRN_OLF")
    comparison_set="LHM P/S seasonal bottoms plus T package rbot=PEIL_T1Z/W retained to compare package versus current HRU DRA bottom authority"
    manifest_sha256=$manifestSha
    collected_utc=(Get-Date).ToUniversalTime().ToString("o")
    collector_host=$env:COMPUTERNAME
    collector_user=$env:USERNAME
    powershell_version=$PSVersionTable.PSVersion.ToString()
    procedure="tools/server/lwkm_collect_dra_remaining.ps1"
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
        status="DRA_REMAINING_Q4_IMMUTABLE_SNAPSHOT"
        bundle_id=$BundleId
        zip_path=$zip
        zip_size_bytes=$zipSize
        zip_sha256=$zipSha
        manifest_sha256=$manifestSha
        payload_file_count=$rows.Count
        payload_bytes=$totalBytes
        zero_unexplained_file_identity_differences=$true
        verified_utc=(Get-Date).ToUniversalTime().ToString("o")
    }
    WriteJson $q4 $result
    $result | ConvertTo-Json -Depth 20
}
finally {
    if (Test-Path -LiteralPath $verify) { Remove-Item -LiteralPath $verify -Recurse -Force }
}
