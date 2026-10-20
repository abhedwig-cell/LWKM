"""Entry point for the standalone offline Windows MET consumer."""
import argparse
from pathlib import Path
from tools.met_grid_consumer import run

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--plan',type=Path);g.add_argument('--spec',type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    if a.spec:
        from tools.bind_met_rasters import bind
        bind(a.spec,a.output/'processing-plan.json')
        a.plan=a.output/'processing-plan.json'
    run(a.plan,a.output)
