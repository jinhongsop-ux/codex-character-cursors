"""Explicit Windows release integration test; preserves pre-test cursor settings.

Usage: python studio/tests/verify_full_release.py <extracted release directory>
Runs installation, reinstall, all live themes, endpoints, reset and file checks.
"""
from pathlib import Path
import ctypes as c
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
import winreg

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import live_verify as v

package = Path(sys.argv[1]).resolve()
home = Path(os.environ['LOCALAPPDATA']) / 'CharacterCursorStudio'
session_path = home / 'session.json'
selection_path = home / 'selection.json'
selection_before = selection_path.read_bytes() if selection_path.exists() else None
v.u.CopyIcon.argtypes = [c.c_void_p]
v.u.CopyIcon.restype = c.c_void_p
v.u.SetSystemCursor.argtypes = [c.c_void_p, c.c_uint]
v.u.SetSystemCursor.restype = c.c_int
v.u.GetBase = v.u.SystemParametersInfoW
runtime = c.c_uint()
assert v.u.GetBase(0x2028, 0, c.byref(runtime), 0)
saved_handles = {role: v.u.CopyIcon(v.u.LoadCursorW(None, c.c_void_p(cid))) for role, cid in v.ROLES.items()}
assert all(saved_handles.values())
keys = [r'Control Panel\Cursors', r'SOFTWARE\Microsoft\Accessibility']
registry_before = {}
for path in keys:
    values = {}
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
        for index in range(winreg.QueryInfoKey(key)[1]):
            name, value, kind = winreg.EnumValue(key, index)
            values[name] = (value, kind)
    registry_before[path] = values

def run(script, flags='--quiet'):
    result = subprocess.run(f'"{os.environ["COMSPEC"]}" /d /s /c ""{package / script}" {flags}"', capture_output=True)
    assert result.returncode == 0, f'{script}: {result.returncode}'

process = None
def start():
    global process
    process = subprocess.Popen([str(home / 'app/CursorStudio.exe'), '--no-browser'])
    for _ in range(100):
        if session_path.exists():
            session = json.loads(session_path.read_text(encoding='utf-8-sig'))
            if session['pid'] == process.pid:
                return
        time.sleep(.1)
    raise RuntimeError('Studio did not start')

def request(path, body=None):
    session = json.loads(session_path.read_text(encoding='utf-8-sig'))
    headers = {'X-Studio-Token': session['token']}
    if body is not None:
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(session['url'] + path, headers=headers,
        data=json.dumps(body).encode() if body is not None else None)
    return urllib.request.urlopen(req, timeout=20).read()

def api(path, body=None):
    return json.loads(request('/api/' + path, body))

try:
    run('检查安装包.cmd')
    # A corrupt file must be rejected, then restore the original bytes.
    usage = package / '使用说明.txt'
    original = usage.read_bytes()
    try:
        usage.write_bytes(original + b'corruption-test')
        result = subprocess.run(f'"{os.environ["COMSPEC"]}" /d /s /c ""{package / "检查安装包.cmd"}" --quiet"', capture_output=True)
        assert result.returncode != 0
    finally:
        usage.write_bytes(original)
    run('检查安装包.cmd')
    print('PASS: original files accepted, corrupted file rejected.')
    with tempfile.TemporaryDirectory(prefix='cursor-skills-') as directory:
        env = os.environ.copy()
        env['CODEX_HOME'] = directory
        result = subprocess.run(f'"{os.environ["COMSPEC"]}" /d /s /c ""{package / "安装制作Skills.cmd"}" --quiet"', env=env, capture_output=True)
        assert result.returncode == 0
        for name in ('character-chibi-prep', 'character-cursor-pack'):
            assert (Path(directory) / 'skills' / name / 'SKILL.md').exists()
    print('PASS: both Skills install to the configured Codex directory.')
    run('一键安装.cmd', '--quiet --no-launch')
    start()
    catalog = api('catalog')
    expected_ids = set(json.loads((package / '文件清单.json').read_text(encoding='utf-8'))['themes'])
    assert {t['id'] for t in catalog['themes']} == expected_ids
    from PIL import Image
    from io import BytesIO
    for theme in catalog['themes']:
        for pixels in (32, 64):
            data = api('apply', {'theme': theme['id'], 'size': pixels})
            assert data['state']['liveSize'] == pixels and data['state']['runtimeBase'] == 32
            values = v.capture()
            for role, cid in v.ROLES.items():
                expected = v.exact_cursor(values[role][0], pixels)
                try:
                    assert v.image_signature(v.u.LoadCursorW(None, c.c_void_p(cid))) == v.image_signature(expected), role
                finally:
                    v.u.DestroyCursor(expected)
                preview = Image.open(BytesIO(request(f'/preview/{theme["id"]}/{role}/{pixels}'))).convert('RGBA')
                raw = Path(values[role][0]).read_bytes()
                bitmap = Image.frombytes('RGBA', (pixels,pixels), raw[62:62+pixels*pixels*4], 'raw','BGRA').transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                for p,q in zip(preview.get_flattened_data(),bitmap.get_flattened_data()):
                    assert p == q or p[3] == q[3] == 0, (theme['id'],role,pixels)
        print('PASS:', theme['id'], 'all 17 live roles, hotspots and preview pixels at 32/64.')
    for pixels in (16,256):
        assert api('apply', {'theme':'pinkhorn','size':pixels})['state']['liveSize'] == pixels
    assert api('reset', {'mode':'default'})['state']['liveSize'] == 32
    assert api('reset', {'mode':'small'})['state']['liveSize'] == 24
    print('PASS: 16/256 endpoints and both reset sizes.')
    run('一键安装.cmd', '--quiet --no-launch')
    process.wait(timeout=10)
    start()
    assert {t['id'] for t in api('catalog')['themes']} == expected_ids
    assert api('apply', {'theme':'pinkhorn','size':64})['state']['liveSize'] == 64
    print('PASS: reinstall and restart retain all themes; no size drift.')
    if '--browser' in sys.argv:
        session = json.loads(session_path.read_text(encoding='utf-8-sig'))
        def browser(command, script=None):
            # Browser daemons can inherit a PIPE on Windows and keep it open.
            with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
                result = subprocess.run('npx --yes agent-browser --session release-ui --json ' + command,
                    shell=True, input=script, encoding='utf-8', stdout=stdout, stderr=stderr, timeout=45)
                assert result.returncode == 0, 'Browser verification command failed'
                stdout.seek(0)
                output = json.loads(stdout.read().decode('utf-8'))
            assert output.get('success'), output
        browser('open ' + session['url'])
        browser('wait --load networkidle')
        browser('eval --stdin', '''(async()=>{
            if(window.CURSOR_MODE!=='local')throw Error('Wrong runtime mode');
            const response=await fetch('/api/catalog',{headers:{'X-Studio-Token':window.STUDIO_TOKEN}});
            const catalog=await response.json();
            if(document.querySelectorAll('.catalog-card').length!==catalog.themes.length)throw Error('Catalog missing');
            document.querySelector('[data-id="pinkhorn"]').click();
            const input=document.querySelector('#sizeInput');input.value=83;input.dispatchEvent(new Event('change'));
            document.querySelector('#applyBtn').click();
            for(let i=0;i<100;i++){if(!document.querySelector('#applyBtn').disabled)break;await new Promise(r=>setTimeout(r,100));}
            if(!document.querySelector('#status').textContent.includes('83 px'))throw Error('Apply did not finish');
            if(!document.querySelector('#deviceInfo').textContent.includes('83 px'))throw Error('Wrong live dimensions');
            document.querySelector('#resetBtn').click();
            for(let i=0;i<100;i++){if(!document.querySelector('#resetBtn').disabled)break;await new Promise(r=>setTimeout(r,100));}
            if(!document.querySelector('#status').textContent.includes('32 px'))throw Error('Reset failed');
            return 'UI apply83 and reset32 passed';
        })()''')
        assert api('state')['liveSize'] == 32
        browser('close')
        print('PASS: actual local UI applies Zero Two at83 and restores system32.')
finally:
    for path, saved in registry_before.items():
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, path) as key:
            current = [winreg.EnumValue(key,i)[0] for i in range(winreg.QueryInfoKey(key)[1])]
            for name in current:
                if name not in saved:
                    winreg.DeleteValue(key,name)
            for name, (value,kind) in saved.items():
                winreg.SetValueEx(key,name,0,kind,value)
    assert v.u.SystemParametersInfoW(0x2029,0,c.c_void_p(runtime.value),3)
    assert v.u.SystemParametersInfoW(0x57,0,None,0)
    for role,handle in saved_handles.items():
        assert v.u.SetSystemCursor(handle,v.ROLES[role])
    if selection_before is None:
        selection_path.unlink(missing_ok=True)
    else:
        selection_path.write_bytes(selection_before)
    if process and process.poll() is None:
        process.terminate()
        process.wait(timeout=10)
    print('RESTORED: pre-test cursor registry, runtime size and all 17 live handles.')
