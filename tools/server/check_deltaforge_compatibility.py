"""Read-only LWKM server compatibility probe; does not install packages or read national rasters."""
import importlib,importlib.metadata,json,platform,sys
from pathlib import Path
PACKAGES={"numpy":"numpy","pandas":"pandas","scipy":"scipy","openpyxl":"openpyxl","yaml":"PyYAML"}
MODULES=["tools.swp_context","tools.modern_swp","tools.swp_renderer","tools.swp_template_adapter",
         "tools.build_modern_population","tools.run_dra_protected_population",
         "tools.hru_population_manifest"]
def check():
    packages={}
    for module,dist in PACKAGES.items():
        try:
            importlib.import_module(module)
            packages[dist]={"status":"IMPORT_OK","version":importlib.metadata.version(dist)}
        except Exception as exc:
            packages[dist]={"status":"IMPORT_FAILED","error":str(exc)}
    modules={}
    for name in MODULES:
        try:
            importlib.import_module(name)
            modules[name]="IMPORT_OK"
        except Exception as exc:
            modules[name]=f"IMPORT_FAILED: {exc}"
    return {"schema_version":1,"python":sys.version,"executable":sys.executable,
        "architecture":platform.architecture()[0],"packages":packages,"modules":modules,
        "changed_environment":False,"ran_model":False}
if __name__=="__main__":
    result=check()
    print(json.dumps(result,indent=2))
    sys.exit(0 if all(v["status"]=="IMPORT_OK" for v in result["packages"].values())
             and all(v=="IMPORT_OK" for v in result["modules"].values()) else 2)
