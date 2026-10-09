"""Rasterize owner-approved source copies for the local film. Originals stay unchanged."""
from pathlib import Path
import hashlib,json
import pymupdf
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT.parent.parent/'draftly-platform'/'inputs'/'case-001'
OUT=ROOT/'public'/'evidence';OUT.mkdir(parents=True,exist_ok=True)
records=[]
def render(number,page=0,rotate=0):
 f=next(SOURCE.glob(f'source-{number:03d}-*.pdf'))
 with pymupdf.open(f) as doc:
  px=doc[page].get_pixmap(matrix=pymupdf.Matrix(2,2),alpha=False)
  im=Image.frombytes('RGB',(px.width,px.height),px.samples)
 if rotate:im=im.rotate(rotate,expand=True)
 return f,im
for name,number,page,rotate in [('title',3,0,0),('instrument',4,1,0),('instrument-cover',4,0,0),('survey',2,0,90),('identity',1,0,0),('resolution',6,0,0),('payment',7,0,0)]:
 f,im=render(number,page,rotate);im.save(OUT/(name+'.png'))
 records.append({'id':name,'sourceNumber':number,'page':page+1,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'method':'Full source raster; no blur or masking. Owner approval confirmed by user.'})
for number,page,rotate,box,name in [(3,0,0,(.565,.316,.9,.335),'title-extent'),(4,1,0,(.19,.348,.735,.375),'instrument-extent'),(2,0,90,(.09,.638,.147,.686),'survey-extent')]:
 f,im=render(number,page,rotate);w,h=im.size
 b=tuple(round(x*(w if i%2==0 else h)) for i,x in enumerate(box))
 im.crop(b).save(OUT/(name+'.png'))
(ROOT/'src/film/evidence-sources.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf8')
print('Owner-approved source display copies prepared without masking. Originals unchanged.')
