exec(open('cursor-studio/tests/verify_native.py',encoding='utf-8-sig').read().split('catalog=api')[0])
try:
 for n in (16,256):
  data=api('apply',{'theme':'pochita','size':n});assert data['state']['liveSize']==n
  for role,cid in v.ROLES.items():
   actual=v.image_signature(v.u.LoadCursorW(None,c.c_void_p(cid)));assert actual[:2]==(n,n)
 print('PASS: range endpoints16 and256, all17 active dimensions.')
finally:api('reset',{'mode':'small'})
