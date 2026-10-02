from pathlib import Path
import json,urllib.request,urllib.error,os,sys,ctypes as c,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent/'tools'));import live_verify as v
session=json.loads((Path(os.environ['LOCALAPPDATA'])/'CharacterCursorStudio/session.json').read_text(encoding='utf-8-sig'))
def request(path,body=None,token=True,origin=None):
 headers={'X-Studio-Token':session['token']} if token else {}
 if body is not None:headers['Content-Type']='application/json'
 if origin:headers['Origin']=origin
 req=urllib.request.Request(session['url']+path,data=json.dumps(body).encode() if body is not None else None,headers=headers)
 with urllib.request.urlopen(req) as r:return r.read()
def api(path,body=None,**kwargs):return json.loads(request('/api/'+path,body,**kwargs))
def rejected(body,**kwargs):
 before=v.capture()
 try:api('apply',body,**kwargs);raise AssertionError('request should be rejected')
 except urllib.error.HTTPError as e:assert e.code in (400,403)
 assert v.capture()==before
# Reproduce the misleading old state: registry32, native runtime128.
assert v.u.SystemParametersInfoW(0x2029,0,c.c_void_p(128),3)
api('apply',{'theme':'reze','size':32})
assert api('state')['runtimeBase']==32
print('PASS: stale runtime128 is normalized to32 before applying32.')
catalog=api('catalog');assert len(catalog['themes'])==4
rejected({'theme':'reze','size':75},token=False);rejected({'theme':'reze','size':75},origin='https://example.com');rejected({'theme':'../','size':75});rejected({'theme':'reze','size':257});rejected({'theme':'reze','size':15})
print('PASS: unauthenticated, cross-origin, invalid theme and size requests do not modify settings.')
try:
 for theme,n in [('reze',75),('rem',96),('deepseek',128),('pochita',192)]:
  data=api('apply',{'theme':theme,'size':n});assert data['state']['liveSize']==n and data['state']['runtimeBase']==32
  values=v.capture()
  for role,cid in v.ROLES.items():
   h=v.exact_cursor(values[role][0],n)
   try:assert v.image_signature(v.u.LoadCursorW(None,c.c_void_p(cid)))==v.image_signature(h),role
   finally:v.u.DestroyCursor(h)
  print('PASS:',theme,n,'all17 live pixels/dimensions/hotspots match generated CUR')
  png=request('/preview/'+theme+'/Arrow/'+str(n));from PIL import Image;from io import BytesIO
  im=Image.open(BytesIO(png)).convert('RGBA');assert im.size==(n,n)
  # Compare the preview directly with the generated DIB bitmap, ignoring invisible RGB.
  import struct
  raw=Path(values['Arrow'][0]).read_bytes();live=Image.frombytes('RGBA',(n,n),raw[62:62+n*n*4],'raw','BGRA').transpose(Image.Transpose.FLIP_TOP_BOTTOM)
  for p,q in zip(im.get_flattened_data(),live.get_flattened_data()):assert p==q or p[3]==q[3]==0
 api('apply',{'theme':'pochita','size':192});assert api('state')['liveSize']==192
 data=api('reset',{'mode':'default'});assert data['state']['liveSize']==32
 import winreg
 with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'SOFTWARE\Microsoft\Accessibility') as k:assert winreg.QueryValueEx(k,'CursorSize')[0]==1 and winreg.QueryValueEx(k,'CursorType')[0]==0
 print('PASS: preview pixels equal CUR bitmap at all four sizes.');print('PASS: repeat apply keeps192; standard reset restores white32 and accessibility size1/type0.')
finally:
 data=api('reset',{'mode':'small'});assert data['state']['liveSize']==24
 print('PASS: small reset24; system left at white-small.')
