"""Source-input DRA diagnostic excluding unresolved drainage spacing.

This tool never emits production files or an admission result. Native source
input versions still need qualification. All HRU members retain full 62500 m2
MODFLOW support. L is excluded until length grids are independently available.
"""
from pathlib import Path
import argparse
import json
import hashlib
import numpy as np
import pandas as pd
from tools.idf_reader import read_idf
from tools.generate_dra import conductance_weighted_depth, repair_system
from tools.p12_swallo import swallo
from tools.regress_dra_cases import discover
from tools.dra_semantic_oracle import parse_dra


def diagnose(membership, ground, river_dir, drain_dir, infiltration, oracle_root):
    oracles = discover(Path(oracle_root))
    members = pd.read_csv(membership)
    members = members[members.HRU.isin(oracles)].copy()
    if members.svat_orig.duplicated().any():
        raise ValueError('Duplicate source SVAT membership')
    if set(members.HRU) != set(oracles):
        raise ValueError('Missing source HRU membership')
    rows = ((625000 - members.y) / 250).astype(int)
    cols = (members.x / 250).astype(int)
    members['glk'] = np.loadtxt(ground, skiprows=6)[rows, cols]
    if (members.glk == -9999).any():
        raise ValueError('Missing ground levels')
    inputs = [Path(membership), Path(ground)]

    def sample(path, fallback=None, nonnegative=False):
        path = Path(path)
        inputs.append(path)
        grid = read_idf(path)
        if (grid.nrow, grid.ncol, grid.xmin, grid.ymin, grid.dx, grid.dy) != (1300, 1200, 0, 300000, 250, 250):
            raise ValueError(f'Unexpected geometry {path}')
        values = grid.values[rows, cols].astype(float)
        if fallback is not None:
            values = np.where(values == grid.nodata, fallback, values)
        return np.maximum(values, 0) if nonnegative else values

    members['infil'] = sample(infiltration, nonnegative=True)
    for sy, name in enumerate(['primair', 'secundair', 'tertiair'], 1):
        key = ['P', 'S', 'T'][sy-1]
        members[f'cdr{sy}'] = sample(Path(river_dir) / f'COND_{name}.IDF', nonnegative=True)
        members[f'inf{sy}'] = sample(Path(river_dir) / f'inf_mz_{name}.IDF', nonnegative=True)
        members[f'bodh{sy}'] = sample(Path(river_dir) / f'steady-state/BODH_{key}1J_250.IDF', members.glk)
        for season, letter in [('sum', 'Z'), ('win', 'W')]:
            members[f'peil_{season}{sy}'] = sample(Path(river_dir) / f'PEIL_{key}1{letter}_250.IDF', members[f'bodh{sy}'])
    for sy, conductance, bottom in [(4, 'COND_buisdrainage.IDF', 'BODH_B_250.IDF'), (5, 'COND_SOF_250.IDF', 'BODH_SOF_250.IDF')]:
        members[f'cdr{sy}'] = sample(Path(drain_dir) / conductance, nonnegative=True)
        members[f'inf{sy}'] = 0
        members[f'bodh{sy}'] = sample(Path(drain_dir) / bottom, members.glk)
        for season in ['sum', 'win']:
            members[f'peil_{season}{sy}'] = members[f'bodh{sy}']
    results = []
    for rid, group in members.groupby('HRU'):
        oracle = parse_dra(oracles[rid].read_text())
        nature = bool(group.lu2_donor.mode().iloc[0] == 2)
        for sy in range(1, 6):
            cdr = group[f'cdr{sy}']
            cs, ins = float(cdr.sum()), float((cdr * group[f'inf{sy}']).sum())
            raw = {'drnres': min(100000, max(1, 62500*len(group)/cs if cs > 0 else 100000)),
                   'infres': min(100000, max(1, 62500*len(group)/ins if ins > 0 else 100000)),
                   'dep': max(0, conductance_weighted_depth(group.glk, group[f'bodh{sy}'], cdr))}
            for season in ['sum', 'win']:
                raw['peil_'+season] = min(max(0, conductance_weighted_depth(group.glk, group[f'peil_{season}{sy}'], cdr)), raw['dep'])
            system = repair_system(raw, sy, nature)
            actual = {'DRARES': float(f"{system['drnres']:.0f}"),
                      'INFRES': float(f"{system['infres']:.0f}"),
                      'ZBOTDR': float(f"{-100*system['dep']:.2f}"),
                      'SWALLO': swallo(sy, system['infres'], float(group.infil.mean()))}
            expected = oracle['systems'][str(sy)]
            differences = {k: {'oracle': expected[k], 'candidate': v} for k, v in actual.items() if expected[k] != v}
            levels = []
            for day, value in expected.get('LEVEL', {}).items():
                season = 'sum' if '-apr-' in day else 'win'
                candidate = float(f"{-100*system['peil_'+season]:.2f}")
                if candidate != value:
                    levels.append({'date': day, 'oracle': value, 'candidate': candidate})
            results.append({'run_id': int(rid), 'system': sy, 'members': len(group), 'nature': nature,
                            'infil_avg': float(group.infil.mean()), 'differences': differences,
                            'level_difference_count': len(levels), 'level_examples': levels[:2]})
    return {'status': 'DIAGNOSTIC_NOT_ADMISSION', 'runs': len(oracles), 'systems': len(results),
            'scalar_mismatch_counts': {k: sum(k in r['differences'] for r in results) for k in ['DRARES', 'INFRES', 'ZBOTDR', 'SWALLO']},
            'level_mismatching_systems': sum(r['level_difference_count'] > 0 for r in results),
            'excluded': 'L: independent length grids unresolved; no production candidate emitted',
            'source_hashes': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in dict.fromkeys(inputs)},
            'cases': results}


def main():
    parser = argparse.ArgumentParser()
    for key in ['membership', 'ground', 'river-dir', 'drain-dir', 'infiltration', 'oracle-root', 'output']:
        parser.add_argument('--'+key, type=Path, required=True)
    args = vars(parser.parse_args())
    output = args.pop('output')
    result = diagnose(**args)
    output.write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k not in ['cases', 'source_hashes']}))


if __name__ == '__main__':
    main()
