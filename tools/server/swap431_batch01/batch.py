#!/usr/bin/env python3
"""LWKM SWAP431 BATCH01: explicit prepare / initial / approve / all lifecycle."""
from __future__ import annotations
import argparse
from collections import Counter, deque
import csv
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback
import uuid
import zipfile

from common import (ROOT, VERSION, SUCCESS, IntegrityError, NotReady, FileLock,
    read_json, atomic_json, immutable_json, file_sha, object_sha, now,
    code_identity, verify_package, distinct_roots, within)
from met07_adapter import load_met07, package, features, select_initial, verify_assets, require
from results import inspect_csv, inspect_logs
from process_guard import WindowsJob


def load_config(path):
    cfg=read_json(path)
    for k in ('source_root','met07_reports','campaign_root','report_root','executable'):
        cfg[k]=str(Path(cfg[k]).resolve())
    require(type(cfg['expected_population']) is int and 0<cfg['expected_population']<=100000,
            'INVALID_POPULATION')
    require(type(cfg['initial_count']) is int and 1<=cfg['initial_count']<=cfg['expected_population'],
            'INVALID_INITIAL_COUNT')
    for k in ('min_free_bytes','per_run_reserve_bytes'):
        require(type(cfg[k]) is int and cfg[k]>=0,'INVALID_SPACE_LIMIT')
    require(math.isfinite(cfg['timeout_seconds']) and cfg['timeout_seconds']>0,'INVALID_TIMEOUT')
    require(isinstance(cfg.get('executable_prefix_args',[]),list),'INVALID_COMMAND_PREFIX')
    protected=[cfg['source_root'],cfg['met07_reports'],cfg['executable'],str(ROOT)]
    protected+=cfg.get('protected_roots',[])
    distinct_roots([cfg['campaign_root'],cfg['report_root']],protected)
    return cfg


def roots(cfg):
    return Path(cfg['campaign_root']),Path(cfg['report_root'])


def gate(cfg):
    status,records,receipts=load_met07(cfg)
    require(file_sha(cfg['executable'])==cfg['executable_sha256'],'EXECUTABLE_DIFFERS_FROM_SIX_TRIALS')
    working=dict(cfg);working['_met07_binding']=status['binding_sha256']
    return working,records,receipts


def campaign_payload(cfg,receipts):
    return dict(schema_version=1,version=VERSION,config=cfg,code_sha256=code_identity(),
                met07_receipt_sha256=receipts,production_enabled=False,
                purpose='unchanged_reference_runs_not_calibration')


def open_campaign(cfg):
    working,records,receipts=gate(cfg); camp,reports=roots(cfg)
    binding=read_json(camp/'CAMPAIGN.json')
    require(binding['identity']==campaign_payload(cfg,receipts),'CAMPAIGN_CODE_CONFIG_OR_UPSTREAM_CHANGED')
    require(object_sha(binding['identity'])==binding['campaign_sha256'],'CAMPAIGN_HASH_MISMATCH')
    for name,sha in binding['prepared_sha256'].items():
        require(file_sha(camp/name)==sha,'PREPARATION_FILE_CHANGED: '+name)
    return working,records,binding


def prepare(cfg):
    camp,reports=roots(cfg);camp.mkdir(parents=True,exist_ok=True);reports.mkdir(parents=True,exist_ok=True)
    with FileLock(camp/'CONTROLLER.lock'):
        try:
            working,records,receipts=gate(cfg)
            if (camp/'CAMPAIGN.json').exists():
                _,_,binding=open_campaign(cfg)
                print('VOORBEREIDING ONGEWIJZIGD HERGEBRUIKT',flush=True)
                return binding
            identity=campaign_payload(cfg,receipts);metadata={}
            for i,(hid,r) in enumerate(sorted(records.items()),1):
                directory,cat,info,text=package(working,r,full=False)
                metadata[hid]=features(directory,cat,text)
                if i%500==0 or i==len(records): print('VOORBEREID %d/%d'%(i,len(records)),flush=True)
            selection=select_initial(metadata,cfg['initial_count'],[int(k) for k in cfg['anchors']])
            atomic_json(camp/'SELECTION_100.json',selection)
            atomic_json(camp/'FEATURES.json',{str(k):v for k,v in metadata.items()})
            total=sum(r['bytes'] for r in records.values())
            initial=sum(records[h]['bytes'] for h in selection['selected_hrus'])
            space=dict(input_copy_bytes_all=total,input_copy_bytes_initial=initial,
                assumed_output_bytes_per_hru=cfg['per_run_reserve_bytes'],
                estimated_initial_bytes=initial+len(selection['selected_hrus'])*cfg['per_run_reserve_bytes'],
                estimated_all_bytes=total+len(records)*cfg['per_run_reserve_bytes'],
                free_bytes_now=shutil.disk_usage(str(camp)).free,
                uncertainty='Output reservation is an operational assumption, not measured national storage. Dispatch checks free space again.',
                initial_hash_scope='All catalogues/manifests and SWP/CRP/CO2; full asset hashes before and after each execution.')
            atomic_json(camp/'PREPARATION.json',space)
            binding=dict(identity=identity,campaign_sha256=object_sha(identity),prepared_utc=now(),
                prepared_sha256={n:file_sha(camp/n) for n in ('SELECTION_100.json','FEATURES.json','PREPARATION.json')})
            immutable_json(camp/'CAMPAIGN.json',binding)
            atomic_json(reports/'STATUS_BATCH.json',dict(status='PREPARED_NO_SWAP_STARTED',
                campaign_sha256=binding['campaign_sha256'],population=len(records),
                selected_hrus=selection['selected_hrus'],swap_executed=False,production_enabled=False))
            for n in ('SELECTION_100.json','PREPARATION.json','CAMPAIGN.json'):shutil.copyfile(camp/n,reports/n)
            print('GEREED. Startbatch=%d; nog geen SWAP gestart.'%len(selection['selected_hrus']),flush=True)
            print('RAPPORTMAP: '+str(reports),flush=True)
            return binding
        except Exception as exc:
            atomic_json(reports/'READINESS_ERROR.json',dict(status='NOT_READY_NO_SWAP_STARTED',
                error=type(exc).__name__+': '+str(exc),time_utc=now(),swap_executed=False))
            raise


def state_path(camp,hid):return camp/'states'/('run_%05d.json'%hid)


def read_states(camp,ids):
    states={}
    for hid in ids:
        p=state_path(camp,hid)
        if p.exists():
            s=read_json(p);require(s['hru']==hid,'STATE_HRU_MISMATCH');states[hid]=s
        else:states[hid]=dict(hru=hid,state='pending',attempts=0)
    return states


def save_state(camp,s):atomic_json(state_path(camp,s['hru']),s)


def validate_completed(cfg,record,s,binding):
    camp,_=roots(cfg);rp=Path(s['result_path'])
    require(within(rp,camp),'RESULT_POINTER_OUTSIDE_CAMPAIGN')
    require(file_sha(rp)==s['result_sha256'],'EXECUTION_RECEIPT_CHANGED')
    r=read_json(rp)
    require(r['hru']==record['hru'] and r['state']=='completed' and r['status']==SUCCESS
            and r['campaign_sha256']==binding['campaign_sha256']
            and r['code_sha256']==binding['identity']['code_sha256']
            and r['executable_sha256']==cfg['executable_sha256'],'RESULT_IDENTITY_MISMATCH')
    _,cat,info,_=package(cfg,record,full=True)
    require(r['input_sha256']=={n:a['sha256'] for n,a in cat['assets'].items()},'RESULT_INPUT_IDENTITY_MISMATCH')
    work=Path(r['work_directory']);verify_assets(work,cat['assets'])
    logs=inspect_logs(work)
    require(r['returncode'] in (0,100) and logs['normal_completion'] and not logs['fatal_messages'],
            'RESULT_COMPLETION_NO_LONGER_VALID')
    for name,spec in r['output_inventory'].items():
        require(file_sha(work/name)==spec['sha256'],'OUTPUT_CHANGED: '+name)
    validation=inspect_csv(work/info['output'],info['start'],info['end'])
    require(validation['sha256']==r['output_validation']['sha256'],'CSV_HASH_CHANGED')
    for name,sha in r.get('summary_sha256',{}).items():
        require(file_sha(Path(r['attempt_directory'])/'analysis'/name)==sha,'DERIVED_SUMMARY_CHANGED: '+name)
    return r


def import_trial(cfg,record,binding):
    """Read original full server output, not the uploaded head/tail fragments."""
    evidence=read_json(ROOT/'evidence'/'trial_imports.json')
    old=evidence.get(str(record['hru']))
    if not old:return None
    work=Path(old['work_directory'])
    if not work.is_dir():return None
    camp,_=roots(cfg);target=camp/'imports'/('run_%05d'%record['hru'])
    source,cat,info,_=package(cfg,record,full=True)
    require(old['input_sha256']=={n:a['sha256'] for n,a in cat['assets'].items()},'PREVIOUS_TRIAL_INPUT_DIFFERS')
    require(old['executable_sha256']==cfg['executable_sha256'],'PREVIOUS_TRIAL_EXECUTABLE_DIFFERS')
    require(file_sha(work/'execution.json')==old['execution_sha256'],'PREVIOUS_TRIAL_RECEIPT_CHANGED')
    execution=read_json(work/'execution.json')
    require(execution['status']==SUCCESS and not execution['errors']
            and execution['input_sha256']==old['input_sha256'],'PREVIOUS_TRIAL_NOT_ACCEPTED')
    verify_assets(work,cat['assets']);logs=inspect_logs(work)
    require(execution['returncode'] in (0,100) and logs['normal_completion'] and not logs['fatal_messages'],
            'PREVIOUS_TRIAL_COMPLETION_INVALID')
    require(file_sha(work/info['output'])==old['output_sha256'],'PREVIOUS_TRIAL_OUTPUT_CHANGED')
    summary=inspect_csv(work/info['output'],info['start'],info['end'],target/'analysis')
    result=dict(execution,state='completed',campaign_sha256=binding['campaign_sha256'],
        code_sha256=binding['identity']['code_sha256'],imported=True,imported_utc=now(),
        import_basis='all_model_input_hashes_and_complete_raw_output_revalidated',
        output_validation=summary,log_validation=logs,attempt_directory=str(target),shared_failure=False,
        executable_sha256=cfg['executable_sha256'],model_success=True,numerical_success=True)
    result['output_inventory']={name:dict(sha256=file_sha(work/name),bytes=(work/name).stat().st_size)
                              for name in [info['output'],*logs['log_sha256']]}
    result['output_bytes']=sum(v['bytes'] for v in result['output_inventory'].values())
    result['summary_sha256']={p.name:file_sha(p) for p in (target/'analysis').iterdir() if p.is_file()}
    atomic_json(target/'EXECUTION.json',result)
    return dict(hru=record['hru'],state='completed',attempts=0,imported=True,
        result_path=str(target/'EXECUTION.json'),result_sha256=file_sha(target/'EXECUTION.json'))


def adopt_result(camp,s,rp,binding):
    r=read_json(rp)
    require(r['hru']==s['hru'] and r['campaign_sha256']==binding['campaign_sha256'], 'WORKER_RESULT_WRONG_CAMPAIGN')
    s.update(state=r['state'],result_path=str(rp),result_sha256=file_sha(rp),
             errors=r['errors'],shared_failure=r['shared_failure'])
    save_state(camp,s);return r


def reconcile(cfg,records,states,binding,selected):
    camp,_=roots(cfg);reused=0;imported=0
    for hid in selected:
        s=states[hid]
        if s['state']=='running':
            # If an old supervisor is still cleaning up, never duplicate its HRU.
            with FileLock(camp/'locks'/('%05d.lock'%hid)):pass
            rp=Path(s['attempt_directory'])/'EXECUTION.json'
            if rp.exists():adopt_result(camp,s,rp,binding)
            else:s.update(state='interrupted',errors=['STALE_RUNNING_NO_COMPLETE_RECEIPT']);save_state(camp,s)
        if s['state']=='pending' and cfg.get('import_previous_trials',True):
            try:
                imp=import_trial(cfg,records[hid],binding)
                if imp:states[hid]=s=imp;save_state(camp,s);imported+=1
            except (IntegrityError,ValueError,OSError) as exc:
                # Evidence mismatch is not a reason to overwrite or silently rerun.
                s.update(state='blocked',errors=['TRIAL_IMPORT_REJECTED: '+str(exc)])
                save_state(camp,s);raise IntegrityError(s['errors'][0])
        if s['state']=='completed':
            try:validate_completed(cfg,records[hid],s,binding);reused+=1
            except Exception as exc:
                s.update(state='blocked',errors=['REUSE_REJECTED: '+str(exc)])
                save_state(camp,s);raise IntegrityError(s['errors'][0])
        if s.get('shared_failure') and s['state']!='completed':
            raise IntegrityError('PREVIOUS_SHARED_FAILURE_REQUIRES_REVIEW: '+str(hid))
        if s['state']=='blocked':raise IntegrityError('BLOCKED_PREVIOUS_INTEGRITY_FAILURE: '+str(hid))
    return reused,imported


def initial_receipt(states,selection):
    return {str(h):states[h]['result_sha256'] for h in selection if states[h]['state']=='completed'}


def approve_all(cfg,confirmed=False):
    require(confirmed,'EXPLICIT_STARTBATCH_REVIEW_REQUIRED')
    camp,reports=roots(cfg)
    with FileLock(camp/'CONTROLLER.lock'):
        working,records,binding=open_campaign(cfg);selection=read_json(camp/'SELECTION_100.json')['selected_hrus']
        states=read_states(camp,records);reconcile(working,records,states,binding,selection)
        require(all(states[h]['state']=='completed' for h in selection),'STARTBATCH_NOT_COMPLETELY_SUCCESSFUL')
        approval=dict(campaign_sha256=binding['campaign_sha256'],
            selection_sha256=binding['prepared_sha256']['SELECTION_100.json'],
            reviewed_results=initial_receipt(states,selection),
            scope='operator_authorizes_expansion_not_scientific_production_admission')
        immutable_json(camp/'APPROVAL_ALL.json',approval)
        print('Uitbreiding expliciet vastgelegd. Geen modelinvoer gewijzigd.',flush=True)


def render_reports(cfg,states,selected,phase,errors,reused=0,imported=0):
    camp,reports=roots(cfg);reports.mkdir(parents=True,exist_ok=True)
    counts=Counter(s['state'] for s in states.values());requested_counts=Counter(states[h]['state'] for h in selected)
    status=dict(status=phase,time_utc=now(),population=len(states),requested=len(selected),
        counts=dict(counts),requested_counts=dict(requested_counts),errors=errors,
        reused_this_invocation=reused,imported_this_invocation=imported,production_enabled=False,
        campaign_root=str(camp),return_zip=str(reports/'SWAP_BATCH_TERUG.zip'))
    atomic_json(reports/'STATUS_BATCH.json',status)
    fields=['hru','state','attempts','imported','elapsed_seconds','returncode','warning_lines',
            'last_date','output_bytes','peak_rss_bytes','read_bytes','write_bytes',
            'BALDEV_max_abs_cm','BALDEV_sum_cm','BALDEV_rms_cm',
            'result_sha256','output_csv_sha256','input_set_sha256','errors']
    native_keys=[k for k in __import__('results').finish(
        {'n':1,'values':{n:dict(total=0.,minimum=0.,maximum=0.,last=0.,squares=0.,abs_total=0.)
                         for n in __import__('results').COLUMNS[1:]}}) if k not in fields]
    fields += native_keys
    tmp=reports/'HRU_SUMMARY.csv.tmp'
    with tmp.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for hid,s in sorted(states.items()):
            row={k:s.get(k,'') for k in ('hru','state','attempts','imported')};r={}
            if s.get('result_path') and Path(s['result_path']).exists():r=read_json(s['result_path'])
            v=r.get('output_validation',{});resource=r.get('observed_resources',{})
            row.update(elapsed_seconds=r.get('elapsed_seconds',''),returncode=r.get('returncode',''),
                warning_lines=r.get('log_validation',{}).get('warning_lines',''),last_date=v.get('last_date',''),
                output_bytes=r.get('output_bytes',''),errors='; '.join(s.get('errors',[])))
            for k in ('peak_rss_bytes','read_bytes','write_bytes'):row[k]=resource.get(k,'')
            for k in ('BALDEV_max_abs_cm','BALDEV_sum_cm','BALDEV_rms_cm',*native_keys):row[k]=v.get('statistics',{}).get(k,'')
            row.update(result_sha256=s.get('result_sha256',''),output_csv_sha256=v.get('sha256',''),
                       input_set_sha256=object_sha(r['input_sha256']) if 'input_sha256' in r else '')
            writer.writerow(row)
    os.replace(str(tmp),str(reports/'HRU_SUMMARY.csv'))
    return status


def bundle(cfg,states):
    camp,reports=roots(cfg);target=reports/'SWAP_BATCH_TERUG.zip';tmp=target.with_suffix('.zip.tmp')
    for name in ('CAMPAIGN.json','SELECTION_100.json','PREPARATION.json','APPROVAL_ALL.json'):
        if (camp/name).is_file():shutil.copyfile(camp/name,reports/name)
    index={}
    with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
        for name in ('STATUS_BATCH.json','HRU_SUMMARY.csv','CAMPAIGN.json','SELECTION_100.json',
                     'PREPARATION.json','APPROVAL_ALL.json','READINESS_ERROR.json'):
            p=reports/name
            if p.is_file():z.write(p,name);index[name]=file_sha(p)
        failed=[s for s in states.values() if s['state'] in ('failed','blocked','interrupted')][:20]
        for s in failed:
            label='failures/run_%05d/'%s['hru'];z.writestr(label+'state.json',json.dumps(s,indent=2))
            rp=Path(s.get('result_path',''))
            if rp.is_file():
                z.write(rp,label+'EXECUTION.json');r=read_json(rp);work=Path(r['work_directory'])
                for name in ('runtime.log','swap.err','swap.log'):
                    p=work/name
                    if p.is_file():
                        with p.open('rb') as f:
                            f.seek(max(0,p.stat().st_size-32768));z.writestr(label+name+'.tail.txt',f.read())
        z.writestr('ARCHIVE_INDEX.json',json.dumps(dict(files=index,failed_logs_limit=20,
            tail_bytes_per_log=32768,raw_model_output_included=False),indent=2))
    os.replace(str(tmp),str(target));print('TERUGSTUREN: '+str(target),flush=True)


def run_batch(cfg,mode='initial',workers=2,retry_failed=False,timeout=None,resume=True):
    camp,reports=roots(cfg);camp.mkdir(parents=True,exist_ok=True);reports.mkdir(parents=True,exist_ok=True)
    require(type(workers) is int and workers>0,'INVALID_WORKERS')
    limit=min(workers,os.cpu_count() or 1,32)
    timeout=cfg['timeout_seconds'] if timeout is None else timeout
    require(math.isfinite(timeout) and 0<timeout<=86400,'INVALID_TIMEOUT')
    with FileLock(camp/'CONTROLLER.lock'):
        working,records,binding=open_campaign(cfg);states=read_states(camp,records)
        selection=read_json(camp/'SELECTION_100.json')['selected_hrus']
        selected=selection if mode=='initial' else sorted(records)
        require(mode in ('initial','all'),'INVALID_MODE')
        if mode=='all':
            approval=read_json(camp/'APPROVAL_ALL.json')
            require(approval['campaign_sha256']==binding['campaign_sha256']
                and approval['selection_sha256']==binding['prepared_sha256']['SELECTION_100.json']
                and len(initial_receipt(states,selection))==len(selection)
                and approval['reviewed_results']==initial_receipt(states,selection),'STARTBATCH_REVIEW_NOT_BOUND')
        atomic_json(camp/'LAST_INVOCATION.json',dict(time_utc=now(),workers_requested=workers,workers_effective=limit,
            timeout_seconds=timeout,mode=mode,retry_failed=retry_failed))
        paused=camp/'PAUSE.json'
        if resume and paused.exists():paused.unlink()
        errors=[];active={};reused=0;imported=0;shared_stop=False;operator_pause=False
        job=WindowsJob();phase='RUNNING';since_report=time.monotonic()
        try:
            reused,imported=reconcile(working,records,states,binding,selected)
            pending=deque(h for h in selected if states[h]['state'] in ('pending','interrupted')
                          or (retry_failed and states[h]['state']=='failed'))
            print('BATCH %s: %d geselecteerd, %d te starten, maximaal %d tegelijk.'%(mode,len(selected),len(pending),limit),flush=True)
            render_reports(cfg,states,selected,'RUNNING',[],reused,imported)
            while pending or active:
                try:
                    if paused.exists():operator_pause=True
                    while pending and len(active)<limit and not shared_stop and not operator_pause:
                        require(file_sha(cfg['executable'])==cfg['executable_sha256'],'EXECUTABLE_CHANGED_DURING_BATCH')
                        reserve=cfg['min_free_bytes']+limit*cfg['per_run_reserve_bytes']
                        if shutil.disk_usage(str(camp)).free<reserve:raise OSError('INSUFFICIENT_SHARED_DISK_SPACE')
                        hid=pending.popleft();s=states[hid]
                        s['attempts']=s.get('attempts',0)+1
                        attempt=camp/'runs'/('run_%05d'%hid)/('try_%03d_%s'%(s['attempts'],uuid.uuid4().hex[:8]))
                        attempt.mkdir(parents=True)
                        task=dict(config=working,record=records[hid],attempt=str(attempt),
                            timeout_seconds=timeout,campaign_sha256=binding['campaign_sha256'],
                            code_sha256=binding['identity']['code_sha256'])
                        atomic_json(attempt/'TASK.json',task)
                        s.update(state='running',attempt_directory=str(attempt),errors=[]);save_state(camp,s)
                        log=(attempt/'worker.log').open('xb')
                        proc=None
                        try:
                            proc=subprocess.Popen([sys.executable,str(ROOT/'worker.py'),'--task',str(attempt/'TASK.json')],
                                stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,close_fds=True,
                                start_new_session=(os.name!='nt'),
                                creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP if os.name=='nt' else 0))
                            job.assign(proc)
                            proc.stdin.write(b'GO\n');proc.stdin.flush()
                        except BaseException:
                            if proc is not None:
                                if proc.stdin:proc.stdin.close()
                                if proc.poll() is None:proc.kill()
                                proc.wait()
                            log.close();s.update(state='interrupted',errors=['SUPERVISOR_LAUNCH_FAILED']);save_state(camp,s)
                            raise
                        active[hid]=(proc,log,attempt);print('START HRU %d (%d actief)'%(hid,len(active)),flush=True)
                    for hid,(proc,log,attempt) in list(active.items()):
                        if proc.poll() is None:continue
                        proc.stdin.close();log.close();del active[hid]
                        rp=attempt/'EXECUTION.json';s=states[hid]
                        if not rp.is_file():
                            s.update(state='interrupted',errors=['WORKER_EXIT_WITHOUT_RESULT: '+str(proc.returncode)])
                            save_state(camp,s);shared_stop=True;errors.append(dict(hru=hid,error=s['errors'][0]))
                            continue
                        r=adopt_result(camp,s,rp,binding)
                        if r['shared_failure']:shared_stop=True;errors.append(dict(hru=hid,errors=r['errors']))
                        print('HRU %d: %s'%(hid,s['state']),flush=True)
                    if time.monotonic()-since_report>=30:
                        render_reports(cfg,states,selected,'DRAINING' if operator_pause or shared_stop else 'RUNNING',errors,reused,imported)
                        since_report=time.monotonic()
                    if (operator_pause or shared_stop) and not active:break
                    if active:time.sleep(.15)
                    elif not pending:break
                except KeyboardInterrupt:
                    if operator_pause:
                        # Close the leases: workers kill their own model and report interrupted.
                        for proc,_,_ in active.values():
                            if not proc.stdin.closed:proc.stdin.close()
                        shared_stop=True
                    operator_pause=True;atomic_json(paused,dict(requested_utc=now(),reason='Ctrl+C'))
                    print('PAUZE: geen nieuwe HRUs; lopende afronden. Nogmaals Ctrl+C onderbreekt lopende HRUs.',flush=True)
                except Exception as exc:
                    shared_stop=True;errors.append(dict(error=type(exc).__name__+': '+str(exc)))
                    print('GEDEELDE STOP: '+str(exc),flush=True)
                    # Let already-running models finish with final integrity checks.
                    if not active:break
                    time.sleep(.2)
            if shared_stop:phase='STOPPED_SHARED_PROBLEM'
            elif operator_pause:phase='PAUSED_AFTER_RUNNING_HRUS'
            elif all(states[h]['state']=='completed' for h in selected):
                phase='INITIAL_BATCH_COMPLETED_NOT_PRODUCTION_ADMITTED' if mode=='initial' else 'REFERENCE_POPULATION_COMPLETED_NOT_PRODUCTION_ADMITTED'
            else:phase='BATCH_FINISHED_WITH_FAILED_OR_UNFINISHED_HRUS'
        except Exception as exc:
            phase='STOPPED_SHARED_PROBLEM';errors.append(dict(error=type(exc).__name__+': '+str(exc)))
        finally:
            # On unexpected controller exceptions close leases, then reap workers.
            for proc,log,attempt in active.values():
                if not proc.stdin.closed:proc.stdin.close()
                try:proc.wait(timeout=15)
                except subprocess.TimeoutExpired:proc.kill();proc.wait()
                log.close()
            job.close()
            for hid,(_,_,attempt) in active.items():
                rp=attempt/'EXECUTION.json'
                if rp.is_file():adopt_result(camp,states[hid],rp,binding)
                else:states[hid].update(state='interrupted');save_state(camp,states[hid])
            status=render_reports(cfg,states,selected,phase,errors,reused,imported);bundle(cfg,states)
        return status


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['prepare','initial','all','approve','pause','status','pack','verify'])
    p.add_argument('--config',type=Path,default=ROOT/'batch_config.json')
    p.add_argument('--workers',type=int,default=2);p.add_argument('--timeout-seconds',type=float)
    p.add_argument('--retry-failed',action='store_true');p.add_argument('--confirmed',action='store_true')
    args=p.parse_args(argv)
    try:
        verify_package()
        if args.action=='verify':print('PACKAGE_HASHES_OK');return 0
        cfg=load_config(args.config);camp,reports=roots(cfg)
        if args.action=='prepare':prepare(cfg)
        elif args.action=='approve':approve_all(cfg,args.confirmed)
        elif args.action=='pause':
            require((camp/'CAMPAIGN.json').is_file(),'CAMPAIGN_NOT_PREPARED')
            atomic_json(camp/'PAUSE.json',dict(requested_utc=now(),reason='operator'))
            print('Pauze gevraagd: lopende HRUs mogen afronden.')
        elif args.action=='status':
            states=read_states(camp,range(1,cfg['expected_population']+1))
            print(json.dumps(dict(Counter(s['state'] for s in states.values())),indent=2))
        elif args.action=='pack':
            with FileLock(camp/'CONTROLLER.lock'):
                states=read_states(camp,range(1,cfg['expected_population']+1))
                selected=read_json(camp/'SELECTION_100.json')['selected_hrus']
                render_reports(cfg,states,selected,'SNAPSHOT_NOT_RECONCILED',[])
                bundle(cfg,states)
        else:
            s=run_batch(cfg,args.action,args.workers,args.retry_failed,args.timeout_seconds)
            return 0 if 'COMPLETED_NOT_PRODUCTION_ADMITTED' in s['status'] else 2
        return 0
    except Exception as exc:
        print('STOP: %s: %s'%(type(exc).__name__,exc),file=sys.stderr)
        return 3

if __name__=='__main__':sys.exit(main())
