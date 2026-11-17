"""Windows job containment and lightweight per-model resource observation."""
from __future__ import annotations
import ctypes
import os
from pathlib import Path
import signal


class WindowsJob:
    """Controller-owned job; hard controller death kills worker/model descendants.

    A worker waits for GO on stdin. The controller first assigns the job, avoiding
    the race where a model could start before containment is installed.
    """
    def __init__(self):
        self.handle = None
        if os.name != 'nt': return
        from ctypes import wintypes as w
        class IO(ctypes.Structure):
            _fields_ = [(k,ctypes.c_ulonglong) for k in
                ('ReadOperationCount','WriteOperationCount','OtherOperationCount',
                 'ReadTransferCount','WriteTransferCount','OtherTransferCount')]
        class BASIC(ctypes.Structure):
            _fields_=[('PerProcessUserTimeLimit',ctypes.c_longlong),('PerJobUserTimeLimit',ctypes.c_longlong),
                ('LimitFlags',w.DWORD),('MinimumWorkingSetSize',ctypes.c_size_t),('MaximumWorkingSetSize',ctypes.c_size_t),
                ('ActiveProcessLimit',w.DWORD),('Affinity',ctypes.c_size_t),('PriorityClass',w.DWORD),('SchedulingClass',w.DWORD)]
        class EXT(ctypes.Structure):
            _fields_=[('BasicLimitInformation',BASIC),('IoInfo',IO),('ProcessMemoryLimit',ctypes.c_size_t),
                ('JobMemoryLimit',ctypes.c_size_t),('PeakProcessMemoryUsed',ctypes.c_size_t),('PeakJobMemoryUsed',ctypes.c_size_t)]
        k=ctypes.WinDLL('kernel32',use_last_error=True); self.k=k
        k.CreateJobObjectW.argtypes=[ctypes.c_void_p,w.LPCWSTR];k.CreateJobObjectW.restype=w.HANDLE
        k.SetInformationJobObject.argtypes=[w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD];k.SetInformationJobObject.restype=w.BOOL
        k.AssignProcessToJobObject.argtypes=[w.HANDLE,w.HANDLE];k.AssignProcessToJobObject.restype=w.BOOL
        k.CloseHandle.argtypes=[w.HANDLE];k.CloseHandle.restype=w.BOOL
        self.handle=k.CreateJobObjectW(None,None)
        if not self.handle: raise ctypes.WinError(ctypes.get_last_error())
        info=EXT();info.BasicLimitInformation.LimitFlags=0x00002000 # KILL_ON_JOB_CLOSE
        if not k.SetInformationJobObject(self.handle,9,ctypes.byref(info),ctypes.sizeof(info)):
            err=ctypes.WinError(ctypes.get_last_error());self.close();raise err
    def assign(self, proc):
        if self.handle and not self.k.AssignProcessToJobObject(self.handle,int(proc._handle)):
            raise ctypes.WinError(ctypes.get_last_error())
    def close(self):
        if self.handle:
            self.k.CloseHandle(self.handle);self.handle=None


def kill_model(proc):
    if proc.poll() is not None: return
    if os.name == 'nt':
        proc.kill() # SWAP has no child processes; controller job contains descendants.
    else:
        try: os.killpg(proc.pid,signal.SIGKILL)
        except ProcessLookupError: pass
    proc.wait()


def resources(proc):
    """Observed process memory and OS I/O counters; absent means unavailable."""
    out={}
    try:
        if os.name == 'nt':
            from ctypes import wintypes as w
            class MEM(ctypes.Structure):
                _fields_=[('cb',w.DWORD),('PageFaultCount',w.DWORD)]+[(n,ctypes.c_size_t) for n in
                    ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage',
                     'QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
            class IO(ctypes.Structure):
                _fields_=[(n,ctypes.c_ulonglong) for n in ('r','w','o','rb','wb','ob')]
            ps=ctypes.WinDLL('psapi',use_last_error=True);k=ctypes.WinDLL('kernel32',use_last_error=True)
            ps.GetProcessMemoryInfo.argtypes=[w.HANDLE,ctypes.c_void_p,w.DWORD]
            k.GetProcessIoCounters.argtypes=[w.HANDLE,ctypes.c_void_p]
            m=MEM();m.cb=ctypes.sizeof(m)
            if ps.GetProcessMemoryInfo(int(proc._handle),ctypes.byref(m),m.cb):out['peak_rss_bytes']=m.PeakWorkingSetSize
            io=IO()
            if k.GetProcessIoCounters(int(proc._handle),ctypes.byref(io)):
                out.update(read_bytes=io.rb,write_bytes=io.wb)
        else:
            p=Path('/proc')/str(proc.pid)
            for line in (p/'status').read_text().splitlines():
                if line.startswith('VmHWM:'):out['peak_rss_bytes']=int(line.split()[1])*1024
            for line in (p/'io').read_text().splitlines():
                key,value=line.split(':',1)
                if key in ('read_bytes','write_bytes'):out[key]=int(value)
    except (OSError,ValueError,AttributeError):
        pass
    return out
