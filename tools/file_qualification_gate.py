"""W00 recursive, consumer-specific production input gate.

Qualification records are authority supplied by the admission process, not
manufactured by the packager. Candidate/research files never pass this gate.
"""
import hashlib
from pathlib import Path


def require_admitted(records, logical_id, consumer, *, _stack=()):
    if logical_id in _stack:
        raise ValueError('cyclic source lineage')
    if logical_id not in records:
        raise ValueError('unregistered input: '+logical_id)
    r=records[logical_id]
    if r.get('qualification_status')!='PRODUCTION_ADMITTED':
        raise ValueError('input not production admitted: '+logical_id)
    if consumer not in r.get('consumers',[]):
        raise ValueError('consumer not admitted: '+logical_id)
    if not r.get('evidence_refs') or not r.get('semantic_contract'):
        raise ValueError('missing qualification evidence/contract: '+logical_id)
    p=Path(r['path'])
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    if h.hexdigest()!=r.get('sha256') or p.stat().st_size!=r.get('size_bytes'):
        raise ValueError('input identity mismatch: '+logical_id)
    if r.get('kind')=='derived':
        if not r.get('parents') or not r.get('code_commit') or not r.get('config_sha256'):
            raise ValueError('incomplete transformation identity: '+logical_id)
        for parent in r['parents']:
            require_admitted(records,parent,r['producer'],_stack=(*_stack,logical_id))
    elif r.get('kind')!='source' or not r.get('provenance'):
        raise ValueError('missing source provenance: '+logical_id)
    return h.hexdigest()
