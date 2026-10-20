# KNMI wind / rainfall-duration raster producer: local Windows dependencies (2026-10-20)

## Context and operating boundary
Local internet-connected Windows PC downloads KNMI daily data and generates two LHM-geometry ASCII raster families: 10-m WIND m/s and WET_RAW positive duration fraction or NODATA. NHI server has no Python and no Internet; completed rasters transfer offline. Do not make corrected WET grids: rain-consistency is enforced later by SWAP MET generation.

KNMI station extraction has been observed successful on the user's Windows PC: 50 stations -> stations_rd.csv. Full historical raster execution and checksums remain unverified.

## Installation and commands
Python 3.10+ is required on the local PC. The raster producer requires numpy, scipy, pyproj:

```cmd
python -m pip install -r requirements.txt
python check_environment.py
run_all.cmd "D:\LWKM_uitwisseling\lwkm_knmi_offline_v2\lwkm_knmi_offline\knmi_downloads"
```

Requirements in the delivered package:
```
numpy>=1.24,<3
scipy>=1.10,<2
pyproj>=3.5,<4
```

The run_all.cmd preflight checks module loading, RD coordinate conversion and SciPy spatial selection **before** downloading station metadata or creating 38,716 daily grids.

## Recorded Windows incident
WindowsApps/python.exe alias did not represent a working installed Python. A loose Deltaforge Python cache could not resolve OpenSSL DLL imports (`import ssl` failed); an old venv pointed to a missing Python executable. With a working local Python, pyproj had to be installed for RD transformation, and numpy/scipy for raster production. Never install downloaded ad hoc DLLs to fix this.

## Planned production QA
Confirm full 1970-2022 coverage (19,358 days * 2 rasters), no duplicates, unchanged template geometry (300x325, 1-km), 50 official station coordinate bindings, valid value ranges, SHA-256 manifests, rerun reuse, sufficient disk space, and meteorological source identity. WET_RAW NODATA means no positive-duration station observation; downstream WET=0 for LHM rain=0 and WET=0.1 for LHM rain>0 with no positive-duration observation. Never call raw duration grid a finished SWAP MET file.

## Status
Preflight and synthetic numerical checks tested locally. User Windows 50-station extraction succeeded. Full production raster generation not yet verified and must not be claimed as admitted.
