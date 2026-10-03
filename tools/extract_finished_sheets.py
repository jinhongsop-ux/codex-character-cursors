"""Extract approved finished sheets without generation; preserve opaque RGB.
Source rectangles and untouched input images live in sources/state-sheets.
Only the outer two-pixel antialias band is mathematically de-matted.
Run: python -X utf8 tools/extract_finished_sheets.py
"""
from pathlib import Path
from collections import deque
import json,hashlib,shutil
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
def background_mask(rgb):
    """Build a deterministic trimap and decontaminate the outer antialias band."""
    w,h=rgb.size; pix=rgb.load(); seen=bytearray(w*h); q=deque()
    def candidate(x,y):
        r,g,b=pix[x,y]
        return min(r,g,b)>=215 and max(r,g,b)-min(r,g,b)<=30
    def seed(x,y):
        i=y*w+x
        if not seen[i] and candidate(x,y): seen[i]=1; q.append((x,y))
    for x in range(w): seed(x,0); seed(x,h-1)
    for y in range(h): seed(0,y); seed(w-1,y)
    while q:
        x,y=q.popleft()
        for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=nx<w and 0<=ny<h:
                i=ny*w+nx
                if not seen[i] and candidate(nx,ny): seen[i]=1; q.append((nx,ny))
    alpha=Image.new('L',(w,h),255); a=alpha.load()
    for y in range(h):
        for x in range(w):
            if seen[y*w+x]: a[x,y]=0
    # The matte around the artwork is almost neutral and light. Keep this
    # conservative: enclosed whites (eyes and clothing) never connect to a cell edge.
    bg_samples=[pix[x,y] for y in range(h) for x in range(w) if seen[y*w+x]]
    if bg_samples:
        bg=tuple(sorted(p[c] for p in bg_samples)[len(bg_samples)//2] for c in range(3))
    else: bg=(245,245,245)

    # Defringe a two-pixel unknown band. The old one-pixel rule left pale
    # antialias pixels stranded just behind dark outlines, visible on dark desktops.
    # A sure foreground pixel is at least one full pixel away from the sure background.
    sure_fg=bytearray(w*h)
    for y in range(h):
        for x in range(w):
            if seen[y*w+x]: continue
            if not any(seen[ny*w+nx] for ny in range(max(0,y-1),min(h,y+2))
                       for nx in range(max(0,x-1),min(w,x+2))):
                sure_fg[y*w+x]=1
    for y in range(h):
        for x in range(w):
            if a[x,y]==0: continue
            if not any(seen[ny*w+nx] for ny in range(max(0,y-2),min(h,y+3))
                       for nx in range(max(0,x-2),min(w,x+3))): continue
            sample=pix[x,y]; d=tuple(sample[k]-bg[k] for k in range(3))
            denom=sum(v*v for v in d)
            if denom<225: a[x,y]=0; continue
            best=None; best_cos=-1
            for ny in range(max(0,y-4),min(h,y+5)):
                for nx in range(max(0,x-4),min(w,x+5)):
                    if not sure_fg[ny*w+nx]: continue
                    fg=pix[nx,ny]; v=tuple(fg[k]-bg[k] for k in range(3)); vn=sum(z*z for z in v)
                    if vn<900: continue
                    dot=sum(d[k]*v[k] for k in range(3))
                    cosine=dot/(denom*vn)**0.5
                    if cosine>best_cos: best_cos=cosine;best=(v,dot,vn)
            if best and best_cos>0.78:
                v,dot,vn=best
                opacity=max(0,min(255,round(255*dot/vn)))
                a[x,y]=min(a[x,y],opacity)
    clean=rgb.copy(); cleaned=clean.load()
    edge_adjusted=0
    # Unmatte only antialiased fringe pixels. Fully opaque art RGB remains exact.
    # This avoids a pale halo when the cursor is shown on a dark desktop.
    for y in range(h):
        for x in range(w):
            opacity=alpha.getpixel((x,y))
            if not 0<opacity<255: continue
            fg=pix[x,y]; a=opacity/255.0
            corrected=tuple(max(0,min(255,round((fg[k]-(1-a)*bg[k])/a))) for k in range(3))
            cleaned[x,y]=corrected;edge_adjusted+=1
    return alpha,clean,edge_adjusted


ROLES=['Arrow','Help','AppStarting','Wait','Crosshair','IBeam','NWPen','No','SizeAll','SizeWE','SizeNESW','UpArrow','SizeNS','SizeNWSE','Hand','Extra']
LABELS=['普通选择','帮助选择','后台工作','忙碌等待','精确选择','文字输入','手写','不可用','移动','水平调整','斜向调整 ↗↙','候选选择','垂直调整','斜向调整 ↖↘','链接选择','额外状态']
def components(alpha):
 w,h=alpha.size;mask=bytearray(int(v>64) for v in alpha.get_flattened_data());groups=[]
 for seed in range(w*h):
  if not mask[seed]:continue
  mask[seed]=0;q=deque([seed]);indices=[]
  while q:
   i=q.popleft();indices.append(i);x,y=i%w,i//w
   for j in [i-1 if x else -1,i+1 if x+1<w else -1,i-w if y else -1,i+w if y+1<h else -1]:
    if j>=0 and mask[j]:mask[j]=0;q.append(j)
  if len(indices)>8:
   xs=[i%w for i in indices];ys=[i//w for i in indices];groups.append((len(indices),(min(xs),min(ys),max(xs)+1,max(ys)+1)))
 return sorted(groups,reverse=True)
def extract():
 source=ROOT/'sources/state-sheets';configs=json.loads((source/'crop-regions.json').read_text(encoding='utf-8'))
 catalog_path=ROOT/'studio/themes/catalog.json';catalog=json.loads(catalog_path.read_text(encoding='utf-8'));font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)
 qa=ROOT/'.release-build/finished-sheets-qa';qa.mkdir(parents=True,exist_ok=True);audits=[]
 for config in configs:
  id=config['id'];im=Image.open(source/f'{id}.png').convert('RGB');out=ROOT/'studio/themes'/id;out.mkdir(parents=True,exist_ok=True);entries=[];canvases=[];records=[]
  for index,role in enumerate(ROLES):
   row,col=divmod(index,4);top,bottom=config['rows'][row];box=(im.width*col//4,top,im.width*(col+1)//4,bottom);raw=im.crop(box);alpha,clean,edges=background_mask(raw)
   if role=='AppStarting':
    centers={'shinobu':(51.5,32.5,14),'rengoku':(35.5,23,10),'mitsuri':(34.5,22.5,10),'tanjiro':(34,22,10)}
    cx,cy,radius=centers[id]
    # Remove only the enclosed paper matte inside the original loading ring.
    for y in range(raw.height):
     for x in range(raw.width):
      rgb=raw.getpixel((x,y))
      if (x-cx)**2+(y-cy)**2<radius**2 and min(rgb)>=215 and max(rgb)-min(rgb)<=30:alpha.putpixel((x,y),0)
   rgba=clean.convert('RGBA');rgba.putalpha(alpha);bounds=alpha.getbbox();assert bounds
   sprite=rgba.crop(bounds);mismatch=sum(a==255 and x!=y for a,x,y in zip(alpha.get_flattened_data(),raw.get_flattened_data(),clean.get_flattened_data()));assert mismatch==0
   if role.startswith('Size'):point=((bounds[0]+bounds[2])/2,(bounds[1]+bounds[3])/2)
   else:
    glyph=alpha.crop((0,0,round(raw.width*.36),round(raw.height*.36)));gb=glyph.point(lambda a:255 if a>96 else 0).getbbox();assert gb,(id,role)
    if role in ['Arrow','UpArrow','Hand','Extra','NWPen']:
     _,x,y=min((x+y,x,y) for y in range(gb[1],gb[3]) for x in range(gb[0],gb[2]) if glyph.getpixel((x,y))>96);point=(x,y)
    else:point=((gb[0]+gb[2]-1)/2,(gb[1]+gb[3]-1)/2)
    if role=='AppStarting':point=centers[id][:2]
   scale=min(464/sprite.width,464/sprite.height);dims=(round(sprite.width*scale),round(sprite.height*scale));offset=((512-dims[0])//2,(512-dims[1])//2)
   canvas=Image.new('RGBA',(512,512));canvas.alpha_composite(sprite.resize(dims,Image.Resampling.LANCZOS),offset);canvas.save(out/f'{role}.png');canvases.append(canvas)
   hx=(offset[0]+(point[0]-bounds[0])*scale)/512;hy=(offset[1]+(point[1]-bounds[1])*scale)/512;assert 0<=hx<1 and 0<=hy<1
   entries.append(dict(role=role,hx=hx,hy=hy));records.append(dict(role=role,source_rect=list(box),sprite_box=list(bounds),opaque_rgb_mismatch_pixels=mismatch,edge_pixels_unmatted=edges,hotspot=[hx,hy]))
   if role=='Arrow':
    groups=components(alpha);body=rgba.copy()
    for _,(l,t,r,b) in groups[1:]:
     if (l+r)/2<raw.width*.36 and (t+b)/2<raw.height*.36:
      ImageDraw.Draw(body).rectangle((max(0,l-2),max(0,t-2),min(raw.width-1,r+1),min(raw.height-1,b+1)),fill=(0,0,0,0))
    character=body.crop(groups[0][1]);character.thumbnail((224,224),Image.Resampling.LANCZOS);basic=Image.new('RGBA',(240,240));basic.alpha_composite(character,((240-character.width)//2,(240-character.height)//2));basic.save(ROOT/'previews/characters'/f'{id}.png')
  extra=entries[-1]
  for alias in ['Pin','Person']:shutil.copy2(out/'Extra.png',out/f'{alias}.png');entries.append(dict(role=alias,hx=extra['hx'],hy=extra['hy']))
  theme=dict(id=id,name=config['name'],roles=entries,sourceWidth=512,category='动漫',tags=['鬼灭之刃','Q版','原图裁切'],summary='保留原图动作与表情的完整角色光标套装。',accent=config['accent'])
  previous=next((i for i,t in enumerate(catalog) if t['id']==id),None)
  if previous is None:catalog.append(theme)
  else:catalog[previous]=theme
  for name,bg in [('light',(247,247,247,255)),('dark',(24,26,31,255)),('black',(0,0,0,255))]:
   contact=Image.new('RGBA',(800,856),bg);draw=ImageDraw.Draw(contact)
   for i,canvas in enumerate(canvases):
    row,col=divmod(i,4);contact.alpha_composite(canvas.resize((176,176),Image.Resampling.LANCZOS),(col*200+12,row*214+5));draw.text((col*200+8,row*214+184),LABELS[i],font=font,fill='white' if name!='light' else '#202027')
   contact.convert('RGB').save(qa/f'{id}-{name}.png')
   if name=='light':contact.convert('RGB').save(ROOT/'previews'/f'{id}.png')
  audits.append(dict(id=id,source_sha256=hashlib.sha256((source/f'{id}.png').read_bytes()).hexdigest(),method='non-generative crop, outside flood-fill, two-pixel edge dematting and conventional resampling',opaque_rgb_mismatch_pixels=0,roles=records,aliases={'Pin':'Extra','Person':'Extra'}))
 catalog_path.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(source/'extraction-audit.json').write_text(json.dumps(audits,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Extracted4 finished sheets;64 source states,72 roleassets; opaque RGB mismatch0; catalog',len(catalog))
if __name__=='__main__':extract()
