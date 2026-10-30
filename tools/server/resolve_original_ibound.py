"""Locate the original MODFLOW layer-1 IBOUND by authoritative BBC09 SHA-256.

The identical original input raster may be used from the historical producer
archive. Never substitute a mask just because its name matches.
"""
from pathlib import Path
import hashlib
import sys
EXPECTED='0e7770f07e7d63a141bd5e268bd28d7aac3d28b56baab29662579113373a4b9f'

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()

def resolve(package_root,model_root):
    package_root=Path(package_root).resolve()
    model_root=Path(model_root).resolve()
    # Search actual MODFLOW input locations first, then original input copy bundled with BBC09.
    parents=[
        model_root.parent/'invoer',model_root.parent/'input',
        model_root.parent/'modflow_input',model_root.parent/'modflow_invoer',
        model_root.parent/'modelinput',model_root.parent/'model_input',
        model_root.parent.parent/'invoer',model_root.parent.parent/'input',
        model_root.parent.parent/'modelinvoer',
        package_root/'source_data',package_root/'tools'/'server'/'source_data',
        package_root,
    ]
    checked=[]
    for parent in parents:
        if not parent.is_dir():continue
        for name in ('IBOUND_L1.IDF','ibound_l1.idf'):
            file=parent/name
            if not file.is_file():continue
            h=sha256(file);checked.append(f'{file} ({h})')
            if h==EXPECTED:return str(file)
    raise FileNotFoundError(
        'Oorspronkelijke MODFLOW IBOUND_L1.IDF niet gevonden met BBC09 SHA256 '+EXPECTED+
        '. Gecontroleerde kandidaten: '+('; '.join(checked) if checked else 'geen')+
        '. Geen willekeurige IBOUND gebruiken.')

if __name__=='__main__':
    try:print(resolve(sys.argv[1],sys.argv[2]))
    except Exception as exc:print(str(exc),file=sys.stderr);sys.exit(2)
