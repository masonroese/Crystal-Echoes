"""Turns a drawn character sheet (any size, the template's 9 x 4 layout, with grid lines) into the
game's 432 x 192 sheet of 48 x 48 cells.
Usage: python3 tools/import_sheet.py art/source/ninja.webp www/sprites/ninja.png

The background can be real transparency, or painted (white or a grey/white checkerboard): a painted
background is removed by flood-filling each cell from its edges through light, colourless pixels.
Every cell is scaled by the same amount and keeps its position, so the animation doesn't jitter:
the middle of each drawn cell becomes the middle of the game cell (the character's position)."""
import sys
from collections import deque
from PIL import Image
import numpy as np
COLS,ROWS,CELL=9,4,48
INSET=7 # source pixels skipped inside each grid line (lines can be ~4 px thick)
src=Image.open(sys.argv[1]).convert('RGBA');a=np.asarray(src).copy()
rgb=a[:,:,:3].astype(int);alpha=a[:,:,3]
painted=(alpha==0).mean()<.05 # no real transparency: the background is painted in
if painted:line=(rgb.mean(axis=2)<190)&(rgb.max(axis=2)-rgb.min(axis=2)<12) # grey grid lines
else:line=alpha>20 # grid lines may be drawn semi-transparent
def grid(frac,n): # the n+1 grid-line positions along one axis
    pos=np.nonzero(frac>.85)[0];cl=[] # grid lines run (almost) the full width/height; sprites never do
    for p in pos:
        if cl and p-cl[-1][-1]<=3:cl[-1].append(p)
        else:cl.append([p])
    c=[sum(g)/len(g) for g in cl]
    pitch=float(np.median([b-a_ for a_,b in zip(c,c[1:])]))
    if len(c)==n: # one outer line too faint to find: add it a cell's width beyond the others
        c=[c[0]-pitch]+c if c[0]>pitch/2 else c+[c[-1]+pitch]
    assert len(c)==n+1,f'expected {n+1} grid lines, found {len(c)} at {[round(x) for x in c]}'
    return c,pitch
XS,pw=grid(line.mean(axis=0),COLS);YS,ph=grid(line.mean(axis=1),ROWS)
print(f'{"painted" if painted else "transparent"} background; cells about {pw:.1f} x {ph:.1f}')
s=CELL/max(pw,ph) # one scale for the whole sheet
def clear_painted(cell):
    c=cell[:,:,:3].astype(int);h,w=c.shape[:2]
    bgish=(c.min(axis=2)>=185)&(c.max(axis=2)-c.min(axis=2)<=10) # light and colourless
    seen=np.zeros((h,w),bool);q=deque([(y,x) for y in range(h) for x in (0,w-1)]+[(y,x) for x in range(w) for y in (0,h-1)])
    while q:
        y,x=q.popleft()
        if seen[y,x] or not bgish[y,x]:continue
        seen[y,x]=True
        for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
            ny,nx=y+dy,x+dx
            if 0<=ny<h and 0<=nx<w and not seen[ny,nx]:q.append((ny,nx))
    cell[seen,3]=0
    return cell
out=Image.new('RGBA',(COLS*CELL,ROWS*CELL),(0,0,0,0))
for r in range(ROWS):
    for c in range(COLS):
        x0,y0=round(XS[c]+INSET),round(YS[r]+INSET);x1,y1=round(XS[c+1]-INSET),round(YS[r+1]-INSET) # just inside the lines
        cell=a[max(0,y0):y1,max(0,x0):x1].copy()
        if painted:cell=clear_painted(cell)
        cell[cell[:,:,3]<16]=0 # drop near-invisible noise
        im=Image.fromarray(cell,'RGBA')
        w,h=max(1,round(im.width*s)),max(1,round(im.height*s))
        small=im.convert('RGBa').resize((w,h),Image.BOX).convert('RGBA') # area-average with premultiplied alpha
        out.alpha_composite(small,(c*CELL+(CELL-w)//2,r*CELL+(CELL-h)//2))
out.save(sys.argv[2],optimize=True)
print('wrote',sys.argv[2],out.size)
