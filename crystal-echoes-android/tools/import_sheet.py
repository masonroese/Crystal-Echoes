"""Turns a drawn character sheet (any size, the template's 9 x 4 layout, transparent background,
optionally with thin grid lines) into the game's 432 x 192 sheet of 48 x 48 cells.
Usage: python3 tools/import_sheet.py art/source/ninja.webp www/sprites/ninja.png

Every cell is scaled by the same amount and keeps its position, so the animation doesn't jitter:
the middle of each drawn cell becomes the middle of the game cell (the character's position)."""
import sys
from PIL import Image
import numpy as np
COLS,ROWS,CELL,INSET=9,4,48,7 # INSET: source pixels skipped inside each grid line (lines can be ~4 px thick)
src=Image.open(sys.argv[1]).convert('RGBA')
a=np.asarray(src)
alpha=a[:,:,3]
# the grid's outer edge: the first and last columns/rows that are mostly opaque (the border lines)
cols=np.nonzero((alpha>128).mean(axis=0)>.5)[0];rows=np.nonzero((alpha>128).mean(axis=1)>.5)[0]
L,Rt,T,B=int(cols[0]),int(cols[-1]),int(rows[0]),int(rows[-1])
pw,ph=(Rt-L)/COLS,(B-T)/ROWS
print(f'grid {L}-{Rt} x {T}-{B}, cells {pw:.1f} x {ph:.1f}')
s=CELL/max(pw,ph) # one scale for the whole sheet
a=a.copy();a[a[:,:,3]<16]=0 # drop near-invisible noise in the background
clean=Image.fromarray(a,'RGBA')
out=Image.new('RGBA',(COLS*CELL,ROWS*CELL),(0,0,0,0))
for r in range(ROWS):
    for c in range(COLS):
        x0,y0=L+c*pw+INSET,T+r*ph+INSET;x1,y1=L+(c+1)*pw-INSET,T+(r+1)*ph-INSET # just inside the grid lines
        cell=clean.crop((round(x0),round(y0),round(x1),round(y1)))
        w,h=max(1,round(cell.width*s)),max(1,round(cell.height*s))
        small=cell.convert('RGBa').resize((w,h),Image.BOX).convert('RGBA') # area-average with premultiplied alpha
        out.alpha_composite(small,(c*CELL+(CELL-w)//2,r*CELL+(CELL-h)//2))
out.save(sys.argv[2],optimize=True)
print('wrote',sys.argv[2],out.size)
