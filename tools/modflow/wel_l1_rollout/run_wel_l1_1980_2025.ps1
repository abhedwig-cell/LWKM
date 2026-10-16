param(
 [string]$Start='1980-01-01',
 [string]$End='1980-01-03',
 [switch]$All,
 [switch]$Overwrite,
 [string]$BaseDir='G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_run_resultaten_totaal\modflow'
)
$ErrorActionPreference='Stop'
if($All){$Start='1980-01-01';$End='2025-12-31'}
$work=Split-Path -Parent $MyInvocation.MyCommand.Path
$source=Join-Path $work 'LWKM_WEL_Uitrol.cs'
$future=Join-Path $work 'variabele_cellen_1980_2025.csv'
$anchors=Join-Path $work 'anker_19791231.csv'
$template=Join-Path $BaseDir 'bdgwel\bdgwel_19791231_l1.idf'
$target=Join-Path $BaseDir 'bdgwel'
foreach($f in @($source,$future,$anchors,$template)){if(!(Test-Path -LiteralPath $f)){throw "Ontbrekend: $f"}}
Add-Type -Path $source -ErrorAction Stop
[LWKM_WEL_Uitrol]::Run($template,$future,$anchors,$target,$Start,$End,[bool]$Overwrite)
