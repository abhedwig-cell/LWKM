"""One independent HRU attempt. No shared status mutation and no input rewrite."""
from __future__ import annotations
import argparse
import errno
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
import traceback
from common import (ROOT, SUCCESS, IntegrityError, FileLock, read_json, atomic_json,
                    file_sha, code_identity, now)
from met07_adapter import package, verify_assets, require
from process_guard import kill_model, resources
from results import inspect_csv, inspect_logs


def execute_task(task, parent_lost):
    cfg=task['config']; hid=task['record']['hru']; attempt=Path(task['attempt'])
    work=attempt/'work'; analysis=attempt/'analysis'
    result=dict(hru=hid,state='failed',status='EXECUTION_FAIL',errors=[],shared_failure=False,
        production_enabled=False,swap_executed=False,started_utc=now(),attempt_directory=str(attempt),
        work_directory=str(work),campaign_sha256=task['campaign_sha256'],code_sha256=task['code_sha256'],
        executable_sha256=cfg['executable_sha256'])
    cat=None;proc=None
    try:
        require(code_identity()==task['code_sha256'],'WORKER_CODE_CHANGED')
        source,cat,info,_=package(cfg,task['record'],full=True)
        result.update(input_sha256={n:a['sha256'] for n,a in cat['assets'].items()},
            input_bytes={n:a['bytes'] for n,a in cat['assets'].items()},
            expected_output_file=info['output'],simulation_start=info['start'],simulation_end=info['end'])
        if parent_lost.is_set():raise InterruptedError('CONTROLLER_DISCONNECTED_BEFORE_START')
        require(file_sha(cfg['executable'])==cfg['executable_sha256'],'EXECUTABLE_CHANGED_BEFORE_START')
        if shutil.disk_usage(str(attempt)).free < cfg['min_free_bytes']+task['record']['bytes']+cfg['per_run_reserve_bytes']:
            raise OSError(errno.ENOSPC,'INSUFFICIENT_FREE_SPACE')
        work.mkdir()
        for name,spec in cat['assets'].items():
            shutil.copyfile(source/name,work/name)
            require(file_sha(work/name)==spec['sha256'],'COPY_HASH_MISMATCH: '+name)
        atomic_json(attempt/'INPUT_BINDING.json',cat)
        args=[cfg['executable']]+cfg.get('executable_prefix_args',[])+['swap']
        result['command']=args
        if parent_lost.is_set():raise InterruptedError('CONTROLLER_DISCONNECTED_BEFORE_LAUNCH')
        begun=time.monotonic(); observed={}; timed_out=False; interrupted=False
        with (work/'runtime.log').open('xb') as log:
            proc=subprocess.Popen(args,cwd=str(work),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
                close_fds=True,start_new_session=(os.name!='nt'))
            result.update(swap_executed=True,model_pid=proc.pid)
            atomic_json(attempt/'MODEL_STARTED.json',dict(pid=proc.pid,started_utc=now()))
            while proc.poll() is None:
                for key,value in resources(proc).items():observed[key]=max(value,observed.get(key,0))
                if parent_lost.is_set():interrupted=True;kill_model(proc);break
                if time.monotonic()-begun>=task['timeout_seconds']:
                    timed_out=True;kill_model(proc);break
                time.sleep(0.1)
            for key,value in resources(proc).items():observed[key]=max(value,observed.get(key,0))
        result.update(returncode=proc.returncode,timed_out=timed_out,interrupted=interrupted,
            elapsed_seconds=time.monotonic()-begun,observed_resources=observed)
        if timed_out:result['errors'].append('TIMEOUT')
        if interrupted:result['errors'].append('CONTROLLER_DISCONNECTED');result['state']='interrupted'
        if proc.returncode not in (0,100):result['errors'].append('RETURN_CODE_'+str(proc.returncode))
        logs=inspect_logs(work);result['log_validation']=logs
        if not logs['normal_completion']:result['errors'].append('NORMAL_COMPLETION_MISSING')
        if logs['fatal_messages']:result['errors'].append('FATAL_MODEL_MESSAGE')
        result['model_success']=not result['errors']
        if logs['normal_completion']:
            try:result['output_validation']=inspect_csv(work/info['output'],info['start'],info['end'],analysis)
            except (ValueError,OSError,UnicodeError) as exc:result['errors'].append(str(exc))
        result['numerical_success']='output_validation' in result
    except InterruptedError as exc:
        result.update(state='interrupted');result['errors'].append(str(exc))
    except IntegrityError as exc:
        result.update(shared_failure=True);result['errors'].append(str(exc))
    except OSError as exc:
        result.update(shared_failure=True);result['errors'].append('SYSTEM_IO: '+str(exc))
    except Exception as exc:
        result.update(shared_failure=True);result['errors'].append(type(exc).__name__+': '+str(exc))
        (attempt/'ERROR.txt').write_text(traceback.format_exc(),encoding='utf-8')
    finally:
        if proc is not None and proc.poll() is None:kill_model(proc)
        if cat is not None:
            try:
                package(cfg,task['record'],full=True);verify_assets(work,cat['assets'])
                require(file_sha(cfg['executable'])==cfg['executable_sha256'],'EXECUTABLE_CHANGED_AFTER_RUN')
                require(code_identity()==task['code_sha256'],'WORKER_CODE_CHANGED_DURING_RUN')
                result['inputs_and_executable_unchanged']=True
            except Exception as exc:
                result.update(shared_failure=True,inputs_and_executable_unchanged=False)
                result['errors'].append('INTEGRITY_AFTER_RUN: '+str(exc))
        if result.get('model_success') and result.get('numerical_success') and not result['errors']:
            result.update(state='completed',status=SUCCESS)
        inventory={}
        try:
            if work.is_dir():
                for p in sorted(work.iterdir()):
                    if p.is_file() and p.name not in (cat['assets'] if cat else {}):
                        inventory[p.name]=dict(sha256=file_sha(p),bytes=p.stat().st_size)
            result['output_inventory']=inventory
            result['output_bytes']=sum(v['bytes'] for v in inventory.values())
            if analysis.is_dir():
                result['summary_sha256']={p.name:file_sha(p) for p in analysis.iterdir() if p.is_file()}
        except Exception as exc:
            result.update(state='failed',status='EXECUTION_FAIL',shared_failure=True)
            result['errors'].append('OUTPUT_INVENTORY_IO: '+str(exc))
        result['finished_utc']=now();atomic_json(attempt/'EXECUTION.json',result)
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--task',type=Path,required=True);a=p.parse_args()
    task=read_json(a.task)
    if sys.stdin.buffer.readline()!=b'GO\n':return 4
    lost=threading.Event()
    def watch_parent():
        try:
            while os.read(sys.stdin.fileno(), 1): pass
        finally:lost.set()
    threading.Thread(target=watch_parent,daemon=True).start()
    try:
        with FileLock(Path(task['config']['campaign_root'])/'locks'/('%05d.lock'%task['record']['hru'])):
            r=execute_task(task,lost)
        return 0 if r['state']=='completed' else 3 if r['shared_failure'] else 4 if r['state']=='interrupted' else 2
    except Exception:
        (Path(task['attempt'])/'WORKER_ERROR.txt').write_text(traceback.format_exc(),encoding='utf-8')
        return 3

if __name__=='__main__':
    # All task receipts have been fsynced and locks released by main. A blocked
    # daemon pipe watcher must not hold interpreter finalization open.
    code=main()
    sys.stdout.flush(); sys.stderr.flush()
    os._exit(code)
