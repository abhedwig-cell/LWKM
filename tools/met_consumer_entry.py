"""Entry point for the standalone offline Windows MET consumer."""
import argparse
from pathlib import Path
from tools.met_grid_consumer import run

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();run(a.plan,a.output)
