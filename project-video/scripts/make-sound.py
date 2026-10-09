"""Original, deterministic film sound design. No third-party recordings."""
from pathlib import Path
import math,random,wave,array
ROOT=Path(__file__).resolve().parents[1]/'public'/'sound'
ROOT.mkdir(parents=True,exist_ok=True)
RATE=24000
def write(name,seconds,fn):
 rng=random.Random(731); samples=array.array('h')
 for i in range(int(RATE*seconds)):
  t=i/RATE; x=max(-.92,min(.92,fn(t,rng)))
  samples.append(round(x*32767))
 with wave.open(str(ROOT/(name+'.wav')),'wb') as f:
  f.setnchannels(1);f.setsampwidth(2);f.setframerate(RATE);f.writeframes(samples.tobytes())
write('folder',1.1,lambda t,r: (.38*math.sin(2*math.pi*72*t)*math.exp(-t*21)+.14*r.uniform(-1,1)*math.exp(-t*35))*min(1,t*800))
write('page',1.3,lambda t,r: .18*r.uniform(-1,1)*math.sin(math.pi*min(1,t/.85))**2*(.65+.35*math.sin(t*59)) if t<.85 else 0)
write('pen',.65,lambda t,r: .11*r.uniform(-1,1)*math.sin(math.pi*min(1,t/.42))**2 if t<.42 else 0)
write('click',.25,lambda t,r: .17*math.sin(2*math.pi*1100*t)*math.exp(-t*90))
# Sparse original piano-like motif; no percussion or speech.
notes=[(0,146.83),(4,220),(8,293.66),(12,196),(16,246.94),(20,164.81),(24,220),(28,293.66)]
def music(t,r):
 local=t%32; value=0
 for start,hz in notes:
  d=local-start
  if 0<=d<8:
   env=min(1,d/.035)*math.exp(-d*.55)
   value+=env*(.16*math.sin(2*math.pi*hz*d)+.045*math.sin(2*math.pi*hz*2*d)+.018*math.sin(2*math.pi*hz*3*d))
 return value
write('score-motif',32,music)
with wave.open(str(ROOT/'score-motif.wav'),'rb') as f:
 motif=f.readframes(f.getnframes())
with wave.open(str(ROOT/'score.wav'),'wb') as f:
 f.setnchannels(1);f.setsampwidth(2);f.setframerate(RATE)
 f.writeframes((motif*21)[:650*RATE*2])
print('Original folder, page, pen, interface and music cues created.')
