"""Find the already identified dqsat raster in existing server directories."""
import json
import os
from pathlib import Path
from tools.server.check_swp_source_values import sha

NAME = 'grensvlak_NHIWQ_v2_fill.asc'
DQSAT_SHA256 = 'e6f13f2308ec55089d384133296fd45e6f796eeefb81260ff8ffebef83f09c3a'


def locate(specs, runs_root, output):
    roots = [Path(specs['glk']['path']).parent,
             Path(specs['glk']['path']).parents[2], runs_root/'LWKM_tools']
    candidates = set()
    explicit = specs.get('dqsat_grid', {}).get('path')
    if explicit:
        candidates.add(Path(explicit))
    manifest = dict(filename=NAME, expected_sha256=DQSAT_SHA256,
                    roots=[str(p) for p in roots], max_directory_depth=5,
                    candidates=[], warnings=[], production_admitted=False)
    # An explicit binding is authoritative; never replace a missing/changed one.
    for root in ([] if explicit else roots):
        if not root.is_dir():
            manifest['warnings'].append(f'directory missing: {root}')
            continue
        def onerror(error):
            manifest['warnings'].append(str(error))
        for directory, subdirs, files in os.walk(root, onerror=onerror):
            path = Path(directory)
            if len(path.relative_to(root).parts) >= 5:
                subdirs[:] = []
            subdirs[:] = [d for d in subdirs if d.lower() not in
                          ('modflow', 'metaswap_results', 'swp_server_productie', '.git', '__pycache__')]
            for name in files:
                if name.lower() == NAME.lower():
                    candidates.add(path/name)
    accepted = []
    for path in sorted(candidates):
        try:
            digest = sha(path)
            record = dict(path=str(path), sha256=digest,
                          status='IDENTIFIED_SOURCE' if digest == DQSAT_SHA256 else 'DIFFERENT_SOURCE_REJECTED')
            if digest == DQSAT_SHA256:
                accepted.append(path)
        except OSError as error:
            record = dict(path=str(path), status='UNREADABLE', error=str(error))
        manifest['candidates'].append(record)
    manifest['selected'] = str(accepted[0]) if accepted else None
    output.write_text(json.dumps(manifest, indent=2)+'\n')
    if not accepted:
        raise ValueError(f'authoritative {NAME} not found; see dqsat_source_manifest.json; '
                         'dqsat_svat.inp is not an approved substitute')
    return accepted[0]
