param([string]$Source = "", [string]$First = "19700110", [string]$Last = "20241231")
$ErrorActionPreference = "Stop"
try {
  if (-not $Source) { $Source = Join-Path (Split-Path $PSScriptRoot -Parent) "LWKM_MetaSWAP_HRU_Windows_x64_1.0.0\metaswap_hru_output" }
  if (-not (Test-Path -LiteralPath $Source -PathType Container)) { throw "Bronmap niet gevonden: $Source. Geef het pad als eerste argument mee." }
  $Dest = Join-Path $PSScriptRoot ("HRU21_export_" + (Get-Date -Format "yyyyMMdd_HHmmss_fff"))
  Write-Host "Bron: $Source"
  Write-Host "Selectie: 21 HRU's, $First t/m $Last. De CSV-bestanden worden gelezen en gehasht."
  & (Join-Path $PSScriptRoot "export_hru21.exe") $Source $Dest (Join-Path $PSScriptRoot "pilot-hrus.csv") $First $Last
  if ($LASTEXITCODE -ne 0) { throw "Export gestopt (code $LASTEXITCODE). Er wordt geen ZIP gemaakt. Bronbestanden zijn niet gewijzigd." }
  if (-not (Test-Path -LiteralPath (Join-Path $Dest "COMPLETE.txt"))) { throw "Volledigheidsbewijs ontbreekt." }
  $Zip = "$Dest.zip"
  Compress-Archive -LiteralPath $Dest -DestinationPath $Zip -CompressionLevel Optimal
  Write-Host "Upload dit bestand: $Zip"
  Write-Host "De exportmap blijft beschikbaar voor controle. Dit is een gegevensselectie; geen kalibratiekwalificatie."
} catch { Write-Error $_; exit 1 }
