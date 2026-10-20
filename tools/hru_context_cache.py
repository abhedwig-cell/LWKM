"""Content-keyed context/SWP cache; unchanged assets are not rendered or rewritten."""
import hashlib
import json
import sqlite3
import zlib


def context_key(context,renderer_identity):
    return hashlib.sha256(json.dumps(dict(context=context,renderer=renderer_identity),sort_keys=True,
        separators=(',',':'),default=str,allow_nan=False).encode()).hexdigest()


def update(records,database,renderer_identity,renderer,*,import_verified=False):
    con=sqlite3.connect(database)
    con.execute('create table if not exists assets (run_id integer primary key, fingerprint text, sha256 text, bytes blob)')
    rows=[];reused=0;generated=0
    try:
        for record in records:
            hid=int(record['run_id']);key=context_key(record['context'],renderer_identity)
            old=con.execute('select fingerprint,sha256,bytes from assets where run_id=?',(hid,)).fetchone()
            if old:
                data=zlib.decompress(old[2])
                if hashlib.sha256(data).hexdigest()!=old[1]:raise ValueError('Corrupt SWP cache')
            if old and old[0]==key:
                digest=old[1];reused+=1
            else:
                data=(record['swp'] if import_verified and old is None else renderer(record['context'])).encode()
                digest=hashlib.sha256(data).hexdigest();generated+=1
                con.execute('insert or replace into assets values (?,?,?,?)',(hid,key,digest,zlib.compress(data)))
            rows.append(dict(run_id=hid,fingerprint=key,swp_sha256=digest,reused=bool(old and old[0]==key)))
        con.commit()
    except Exception:
        con.rollback();raise
    finally:con.close()
    return dict(count=len(rows),reused=reused,written=generated,rows=rows,production_admitted=False)
