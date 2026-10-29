from tools.accept_swp_source_inventory import confirmed_locations


def ref(key,path):
    return dict(key=key,locations=[dict(path=path,status='FILE_EXISTS')],control='control.ini',line=2,control_sha256='abc',provenance='PREVIOUSLY_UPLOADED_RUN_CONFIG')


def test_location_binding_preserves_units_and_rejects_conflict():
    report=dict(references=[ref('maaiveld_asc',r'E:\model\ahn_cm.asc'),ref('rootzone_asc',r'E:\model\root.asc'),ref('rootzone_asc',r'E:\other\root.asc')],
                known_output_locations=[dict(status='FILE_EXISTS',path=r'G:\output\head_19700101000000_l1.idf')],controls=[])
    r=confirmed_locations(report)
    assert r['sources']['glk']['units']=='NOT_YET_VERIFIED'
    assert r['sources']['head']['date']=='1970-01-01'
    assert r['unresolved']['rds']['reason']=='MULTIPLE_EXISTING_PATHS'
