"""Prepare a portable W03-W06 plan from explicitly selected recovered sources."""
import argparse
import shutil
from pathlib import Path
import zipfile
from tools.hru_source_chain import sha,atomic_json,SOURCE_SHA
from tools.run_current_data_reconstruction import exact_basename_member


EXPECTED={'base_svat':'5f7b657508a4dc885bd60fae93051239046b27788388d6e8832621eaa85fe192',
          'processed_svat':'5ea4d24a0ce38c802cb1dbf63e30239664965438fbcc55690acced447a248821',
          'ldgb':'c659530fb69e32af5fe309b7ae80e20b470e88094b92569f851a32321182d21e'}


def prepare(base_svat,processed_svat,ldgb,workbook,csv_zip,lhm2swap_zip,template,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);inputs=output/'inputs';inputs.mkdir(exist_ok=True)
    records={};archives={}
    def bind(name,p,origin,parent=None):
        digest=sha(p)
        if name in EXPECTED and digest!=EXPECTED[name]:raise ValueError('Unexpected HRU10242 input: '+name)
        dest=inputs/(name+Path(p).suffix)
        if dest.exists():
            if sha(dest)!=digest:raise ValueError('Existing plan contains changed input')
        else:shutil.copyfile(p,dest)
        records[name]=dict(path=str(dest.relative_to(output)),sha256=digest,logical_id='LWKM_HRU10242_'+name.upper(),
            semantic_role=name,source_location=origin,source_version='HRU10242_recovered_snapshot',
            qualification_status='PROVENANCE_BOUND_FOR_RECONSTRUCTION',parent=parent,
            consumer='tools.hru_source_chain / tools.qualify_hru_replay')
    for name,p in [('base_svat',base_svat),('processed_svat',processed_svat),('ldgb',ldgb),('workbook',workbook),('template',template)]:bind(name,Path(p),Path(p).name)
    for archive,names in [(csv_zip,{'reference_membership':'export_svat_HRU_NRU_10242.csv','reference_schema':'export_HRUschema_10242.csv'}),
            (lhm2swap_zip,{'landuse_lookup':'lu2lwkm.csv','svat_raster':'svat_LHM43.asc','historical_filter':'filter_lwkm2.asc'})]:
        archive=Path(archive);digest=sha(archive);archives[archive.name]=digest
        with zipfile.ZipFile(archive) as z:
            for name,basename in names.items():
                member=exact_basename_member(z,basename);p=inputs/('extract-'+basename)
                with z.open(member) as a,p.open('wb') as b:shutil.copyfileobj(a,b)
                bind(name,p,archive.name+'/'+member,dict(archive_sha256=digest,member=member));p.unlink()
    source=Path(__file__).with_name('legacy')/'HRU_clustering_LWKM20_31082026.R'
    if sha(source)!=SOURCE_SHA:raise ValueError('Historical source changed')
    bind('r_source',source,'Rscripts.zip/Rscripts/HRU_clustering/'+source.name)
    plan=dict(schema_version=1,policy='HISTORICAL_31082026_REPLAY_NOT_ADMISSION',inputs=records,
        archive_sha256=archives,producer_code_sha256=sha(Path(__file__)))
    atomic_json(output/'plan.json',plan);return plan


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['base_svat','processed_svat','ldgb','workbook','csv_zip','lhm2swap_zip','template','output']:
        p.add_argument('--'+n.replace('_','-'),type=Path,required=True)
    prepare(**vars(p.parse_args()))
