"""Explicit live install/reinstall/restore test; can leave the theme applied.

Run only when applying the user's cursor theme is authorized.
"""
import ctypes as c
from ctypes import wintypes as w
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import struct
import winreg
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
ROLES={'Arrow':32512,'Help':32651,'AppStarting':32650,'Wait':32514,
       'Crosshair':32515,'IBeam':32513,'NWPen':32631,'No':32648,
       'SizeAll':32646,'SizeWE':32644,'SizeNESW':32643,'UpArrow':32516,
       'SizeNS':32645,'SizeNWSE':32642,'Hand':32649,'Pin':32671,'Person':32672}
SYSTEM_ROLES={k:v for k,v in ROLES.items() if k not in ('Pin','Person')}

u=c.WinDLL('user32',use_last_error=True)
g=c.WinDLL('gdi32',use_last_error=True)
class IconInfo(c.Structure):
    _fields_=[('icon',w.BOOL),('x',w.DWORD),('y',w.DWORD),('mask',w.HBITMAP),('color',w.HBITMAP)]
class Bitmap(c.Structure):
    _fields_=[('type',w.LONG),('width',w.LONG),('height',w.LONG),('stride',w.LONG),('planes',w.WORD),('bits',w.WORD),('data',c.c_void_p)]
class Header(c.Structure):
    _fields_=[('size',w.DWORD),('width',w.LONG),('height',w.LONG),('planes',w.WORD),('bits',w.WORD),('compression',w.DWORD),('bytes',w.DWORD),('x',w.LONG),('y',w.LONG),('colors',w.DWORD),('important',w.DWORD)]
u.LoadCursorW.argtypes=[w.HINSTANCE,c.c_void_p];u.LoadCursorW.restype=w.HANDLE
u.LoadImageW.argtypes=[w.HINSTANCE,w.LPCWSTR,w.UINT,c.c_int,c.c_int,w.UINT];u.LoadImageW.restype=w.HANDLE
u.GetIconInfo.argtypes=[w.HANDLE,c.POINTER(IconInfo)]
u.DestroyCursor.argtypes=[w.HANDLE]
u.SystemParametersInfoW.argtypes=[w.UINT,w.UINT,c.c_void_p,w.UINT]
u.SystemParametersInfoW.restype=w.BOOL
g.GetObjectW.argtypes=[w.HANDLE,c.c_int,c.c_void_p]
g.DeleteObject.argtypes=[w.HANDLE]
g.CreateCompatibleDC.argtypes=[w.HDC];g.CreateCompatibleDC.restype=w.HDC
g.DeleteDC.argtypes=[w.HDC]
g.GetDIBits.argtypes=[w.HDC,w.HBITMAP,w.UINT,w.UINT,c.c_void_p,c.c_void_p,w.UINT]

def image_signature(handle):
    info=IconInfo()
    assert handle and u.GetIconInfo(handle,c.byref(info))
    dc=None
    try:
        bm=Bitmap()
        assert info.color and g.GetObjectW(info.color,c.sizeof(bm),c.byref(bm))
        header=Header(c.sizeof(Header),bm.width,-bm.height,1,32,0,0,0,0,0,0)
        data=(c.c_ubyte*(bm.width*bm.height*4))()
        dc=g.CreateCompatibleDC(None)
        assert g.GetDIBits(dc,info.color,0,bm.height,data,c.byref(header),0)==bm.height
        return (bm.width,bm.height,info.x,info.y,hashlib.sha256(bytes(data)).hexdigest())
    finally:
        if dc:g.DeleteDC(dc)
        if info.mask:g.DeleteObject(info.mask)
        if info.color:g.DeleteObject(info.color)

def capture():
    result={}
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Control Panel\Cursors') as key:
        for role in list(ROLES)+['','Scheme Source','CursorBaseSize']:
            try: result[role]=winreg.QueryValueEx(key,role)
            except FileNotFoundError: result[role]=None
    return result

def run(mode):
    p=subprocess.run([str(ROOT/'package/RezeCursor.exe'),mode,'--quiet'],capture_output=True)
    if p.returncode: raise RuntimeError(f'{mode} failed: '+p.stderr.decode('utf-8',errors='replace'))
    print('PASS:',mode)

def exact_cursor(path,n):
    data=Path(path).read_bytes()
    count=struct.unpack_from("<H",data,4)[0]
    entries=[struct.unpack_from("<BBBBHHII",data,6+i*16) for i in range(count)]
    e=min(entries,key=lambda e:abs((e[0] or 256)-n))
    bits=struct.pack("<HH",e[4],e[5])+data[e[7]:e[7]+e[6]]
    fn=u.CreateIconFromResourceEx
    fn.argtypes=[c.c_void_p,w.DWORD,w.BOOL,w.DWORD,c.c_int,c.c_int,w.UINT];fn.restype=w.HANDLE
    return fn(bits,len(bits),False,0x30000,n,n,0)

def verify_applied():
    values=capture()
    for role,cid in SYSTEM_ROLES.items():
        path=values[role][0]
        assert 'RezeCursor' in path and Path(path).is_file()
        actual=image_signature(u.LoadCursorW(None,c.c_void_p(cid)))
        expected_handle=exact_cursor(path,actual[0])
        try: assert actual==image_signature(expected_handle),(role,actual,image_signature(expected_handle))
        finally:
            if expected_handle:u.DestroyCursor(expected_handle)
    # Pin and Person have registry files but no documented SetSystemCursor IDs.
    for role in ('Pin','Person'):
        assert Path(values[role][0]).is_file()
    print('PASS: 15 documented live system cursors match the installed pixels and hotspots; Pin/Person files are present.')

def refresh_live():
    # Refresh this verifier process too, so LoadCursor does not compare stale shared handles.
    if not u.SystemParametersInfoW(0x57,0,None,0):
        raise RuntimeError('Windows could not refresh cursors during verification.')

def verify_active_matches_registry():
    # Run this in a fresh process after restore. LoadCursor can retain shared
    # handles from before SPI_SETCURSORS in the process that performed the test.
    values=capture()
    for role,cid in ROLES.items():
        path=values[role][0]
        actual=image_signature(u.LoadCursorW(None,c.c_void_p(cid)))
        expected_size=values["CursorBaseSize"][0] if values["CursorBaseSize"] else 32
        assert actual[:2]==(expected_size,expected_size),(role,actual[:2],expected_size)
        expected_handle=u.LoadImageW(None,path,2,expected_size,expected_size,0x10)
        try:
            assert actual==image_signature(expected_handle),(role,actual,image_signature(expected_handle))
        finally:
            if expected_handle:u.DestroyCursor(expected_handle)
    print('PASS: 17 restored live system cursors (including exact restored dimensions) match their configured files and hotspots.')

def snapshot_from_xml(data):
    kinds={'String':winreg.REG_SZ,'ExpandString':winreg.REG_EXPAND_SZ,
           'Binary':winreg.REG_BINARY,'DWord':winreg.REG_DWORD,
           'MultiString':winreg.REG_MULTI_SZ,'QWord':winreg.REG_QWORD}
    root=ET.fromstring(data)
    result={}
    for entry in root.findall('./Entries/Entry'):
        name=entry.findtext('Name')
        if entry.findtext('Exists','false').lower()!='true':
            result[name]=None
        else:
            kind=entry.findtext('Kind','String')
            value=entry.findtext('Value')
            if kind=='DWord':value=int(value)
            elif kind=='QWord':value=int(value)
            result[name]=(value,kinds[kind])
    return result

def main():
    if '--verify-active-registry' in sys.argv:
        verify_active_matches_registry()
        return
    if '--apply-test' not in sys.argv:
        raise SystemExit('Requires --apply-test: temporarily changes the current cursor theme.')
    before=capture()
    backup=Path(os.environ['LOCALAPPDATA'])/'RezeCursor/original.xml'
    initial_backup=backup.read_bytes() if backup.exists() else None
    installed=False
    report={'version':'1.4.1','utc':datetime.now(timezone.utc).isoformat()}
    try:
        run('install');installed=True
        verify_applied();report['live_install_roles']=17
        saved=backup.read_bytes()
        saved_size=(backup.parent/"original-size.xml").read_bytes()
        if initial_backup is not None:assert saved==initial_backup
        run('install');verify_applied()
        assert backup.read_bytes()==saved
        report['repeat_install_preserves_backup']=True
        run('restore');installed=False
        restored_registry=capture()
        expected_restore=snapshot_from_xml(saved)
        expected_restore.update(snapshot_from_xml(saved_size))
        if restored_registry!=expected_restore:
            differing=[k for k in expected_restore if expected_restore[k]!=restored_registry.get(k)]
            raise AssertionError('Restored registry differs from the original backup for '+', '.join(differing))
        probe=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--verify-active-registry'],capture_output=True,text=True)
        if probe.returncode:
            raise AssertionError('Restored live cursors do not match their configured files: '+probe.stderr.strip())
        print(probe.stdout.strip())
        report['exact_registry_and_live_restore']=True
        report['live_roles_verified']=len(SYSTEM_ROLES)
        print('PASS: registry values/types and 15 documented live cursor pixels restored exactly.')
        if '--leave-installed' in sys.argv:
            run('install');installed=True;verify_applied()
        report['left_installed']=installed
        (ROOT/'tests/live-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    except:
        if installed:run('restore')
        raise

if __name__=='__main__':main()
