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
if src.size==(COLS*CELL,ROWS*CELL): # already drawn at game size: copy it, minus any leftover faint grid lines
    for axis in (0,1):
        b=a if axis==0 else a.transpose(1,0,2) # axis 0: rows, axis 1: columns
        for i in range(1,b.shape[0]-1):
            row=b[i];vis=row[:,3]>0
            if (vis.mean()>.85) and np.median(row[vis,3])<100: # a faint line all the way across
                solid=(b[i-1,:,3]>=16)|(b[i+1,:,3]>=16)
                row[solid]=b[i-1][solid];row[~solid]=0 # inside a sprite take the pixel above, elsewhere erase
    Image.fromarray(a,'RGBA').save(sys.argv[2],optimize=True);print('game-size sheet: copied',sys.argv[2]);sys.exit()
rgb=a[:,:,:3].astype(int);alpha=a[:,:,3]
painted=(alpha==0).mean()<.05 # no real transparency: the background is painted in
if painted:line=(rgb.mean(axis=2)<190)&(rgb.max(axis=2)-rgb.min(axis=2)<12) # grey grid lines
else:line=alpha>20 # grid lines may be drawn semi-transparent
def grid(frac,n,ink): # the n+1 cell edges along one axis
    pos=np.nonzero(frac>.85)[0];cl=[] # grid lines run (almost) the full width/height; sprites never do
    for p in pos:
        if cl and p-cl[-1][-1]<=3:cl[-1].append(p)
        else:cl.append([p])
    c=[sum(g)/len(g) for g in cl]
    if len(c)<n-1: # no grid lines: cut at the emptiest line near each expected edge (the gaps between frames)
        global gridless;gridless=True
        size=len(ink);step=size/n;cuts=[0]
        for k in range(1,n):
            lo,hi=int(step*(k-.3)),int(step*(k+.3));cuts.append(lo+int(np.argmin(ink[lo:hi])))
        cuts.append(size);inner=float(np.median([b-a_ for a_,b in zip(cuts[1:-1],cuts[2:-1])])) if n>2 else step
        cuts[0]=max(0,cuts[1]-inner);cuts[-1]=min(size,cuts[-2]+inner) # outer cells the same size as the inner ones
        return cuts,inner
    while len(c)>n+1: # extra candidates (a full-width streak of effects): drop whichever leaves the most even spacing
        c=min((c[:i]+c[i+1:] for i in range(len(c))),key=lambda d:np.std(np.diff(d)))
    pitch=float(np.median([b-a_ for a_,b in zip(c,c[1:])]))
    if len(c)==n: # one outer line too faint to find: add it a cell's width beyond the others
        c=[c[0]-pitch]+c if c[0]>pitch/2 else c+[c[-1]+pitch]
    assert len(c)==n+1,f'expected {n+1} grid lines, found {len(c)} at {[round(x) for x in c]}'
    return c,pitch
gridless=False
ink=alpha>40 if not painted else ~((rgb.min(axis=2)>=185)&(rgb.max(axis=2)-rgb.min(axis=2)<=10)) # pixels that are part of the art
XS,pw=grid(line.mean(axis=0),COLS,ink.sum(axis=0));YS,ph=grid(line.mean(axis=1),ROWS,ink.sum(axis=1))
print(f'{"painted" if painted else "transparent"} background; cells about {pw:.1f} x {ph:.1f}; cuts x {[round(x) for x in XS]} y {[round(y) for y in YS]}')
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
def place(region,cx,cy,rx,ry,c,r): # scale a source region and put it so the source point (cx,cy) lands on the cell centre
    im=Image.fromarray(region,'RGBA');w,h=max(1,round(im.width*s)),max(1,round(im.height*s))
    small=im.convert('RGBa').resize((w,h),Image.BOX).convert('RGBA') # area-average with premultiplied alpha
    tile=Image.new('RGBA',(CELL,CELL),(0,0,0,0));tile.alpha_composite(small,(round(CELL/2-(cx-rx)*s),round(CELL/2-(cy-ry)*s)))
    out.alpha_composite(tile,(c*CELL,r*CELL))
if gridless:
    # Without lines, a frame's effects can spill past the gap between frames. So each connected piece of art
    # belongs to the cell that holds its centre, and is taken whole; faint glow outside any piece stays in its cell.
    from scipy import ndimage
    strong=a[:,:,3]>100;lab,nl=ndimage.label(strong,structure=np.ones((3,3)))
    cent=ndimage.center_of_mass(strong,lab,range(1,nl+1))
    rowcut=lambda y:max(0,min(ROWS-1,int(np.searchsorted(YS,y,side='right'))-1))
    colcuts=[] # each row band gets its own column cuts, from that band's own gaps
    for r in range(ROWS):
        band=ink[int(YS[r]):int(YS[r+1])].sum(axis=0);colcuts.append(grid(np.zeros(len(band)),COLS,band)[0])
    owner=np.zeros(nl+1,int)-1
    for i,(cy,cx) in enumerate(cent,1):
        r=rowcut(cy);c=max(0,min(COLS-1,int(np.searchsorted(colcuts[r],cx,side='right'))-1));owner[i]=r*COLS+c
    for i,sl in enumerate(ndimage.find_objects(lab),1): # a piece joining two frames (effects touching): split it at the cell edges
        if sl[1].stop-sl[1].start>.9*pw or sl[0].stop-sl[0].start>.9*ph:owner[i]=-2
    own=owner[lab] # cell index for every strong pixel (-2: decided by position)
    H,W=a.shape[:2]
    for r in range(ROWS):
        for c in range(COLS):
            X0,X1,Y0,Y1=colcuts[r][c],colcuts[r][c+1],YS[r],YS[r+1]
            m=int(.4*max(X1-X0,Y1-Y0));rx,ry=max(0,int(X0)-m),max(0,int(Y0)-m);rx1,ry1=min(W,int(X1)+m),min(H,int(Y1)+m)
            reg=a[ry:ry1,rx:rx1].copy();o=own[ry:ry1,rx:rx1];st=strong[ry:ry1,rx:rx1]
            yy,xx=np.mgrid[ry:ry1,rx:rx1];inside=(xx>=X0)&(xx<X1)&(yy>=Y0)&(yy<Y1)
            keep=np.where(st,(o==r*COLS+c)|((o==-2)&inside),inside) # whole pieces that belong here, plus anything else inside the cell
            reg[~keep]=0;reg[reg[:,:,3]<16]=0
            if reg[:,:,3].any():place(reg,(X0+X1)/2,(Y0+Y1)/2,rx,ry,c,r)
else:
    for r in range(ROWS):
        for c in range(COLS):
            x0,y0=round(XS[c]+INSET),round(YS[r]+INSET);x1,y1=round(XS[c+1]-INSET),round(YS[r+1]-INSET) # just inside the lines
            cell=a[max(0,y0):y1,max(0,x0):x1].copy()
            if painted:cell=clear_painted(cell)
            cell[cell[:,:,3]<16]=0 # drop near-invisible noise
            im=Image.fromarray(cell,'RGBA');w,h=max(1,round(im.width*s)),max(1,round(im.height*s))
            small=im.convert('RGBa').resize((w,h),Image.BOX).convert('RGBA')
            out.alpha_composite(small,(c*CELL+(CELL-w)//2,r*CELL+(CELL-h)//2)) # centred in its cell
out.save(sys.argv[2],optimize=True)
print('wrote',sys.argv[2],out.size)
