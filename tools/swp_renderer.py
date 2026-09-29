"""Generic SWP template renderer.

No LWKM-specific defaults live here. Context must already be fully resolved.
Supports scalar {{X}}, repeated {{#TABLE}}...{{/TABLE}}, and boolean/conditional blocks.
"""
from __future__ import annotations
import re
from pathlib import Path

TOKEN=re.compile(r"{{\s*([#/]?)([A-Za-z0-9_]+)\s*}}")

def _render(text:str,ctx:dict)->str:
    # resolve sections recursively, innermost by matching name
    while True:
        m=re.search(r"{{\s*#([A-Za-z0-9_]+)\s*}}",text)
        if not m: break
        name=m.group(1); start=m.end()
        endm=re.search(r"{{\s*/"+re.escape(name)+r"\s*}}",text[start:])
        if not endm: raise ValueError(f"Unclosed section {name}")
        a=m.start(); b=start+endm.start(); z=start+endm.end()
        body=text[start:b]; value=ctx.get(name)
        if isinstance(value,list):
            repl="".join(_render(body,{**ctx,**row}) for row in value)
        elif value:
            repl=_render(body,ctx)
        else: repl=""
        text=text[:a]+repl+text[z:]
    unresolved_sections=re.findall(r"{{\s*/([A-Za-z0-9_]+)\s*}}",text)
    if unresolved_sections: raise ValueError(f"Unexpected closing sections {unresolved_sections}")
    def sub(m):
        sig,name=m.groups()
        if sig: raise ValueError(f"Unexpected section token {m.group(0)}")
        if name not in ctx or ctx[name] is None: raise KeyError(f"Unresolved template symbol {name}")
        return str(ctx[name])
    out=TOKEN.sub(sub,text)
    leftovers=re.findall(r"{{[^}]+}}",out)
    if leftovers: raise ValueError(f"Unsupported/unresolved template tokens: {leftovers[:10]}")
    return out

def render_text(template:str,context:dict)->str:
    return _render(template,context)

def render_file(template_path:Path,output_path:Path,context:dict)->None:
    rendered=render_text(template_path.read_text(encoding="utf-8",errors="replace"),context)
    output_path.parent.mkdir(parents=True,exist_ok=True)
    tmp=output_path.with_suffix(output_path.suffix+".tmp")
    tmp.write_text(rendered,encoding="utf-8",newline="\n")
    tmp.replace(output_path)
