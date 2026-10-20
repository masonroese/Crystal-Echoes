"""Draws the blank character sprite-sheet template (run once; the output is committed).
Usage: python3 tools/make_sprite_template.py   (from crystal-echoes-android/)

Writes art/sprite-template.png        432x192, actual size: faint guides only, to use as a layer under the art
       art/sprite-template-guide.png  4x size, labelled, for reference

Layout (48x48 cells, art faces right, the game mirrors it for left; the cell centre is the character's position):
  row 1: idle, damaged, death
  row 2: walk right 1-3, walk up 1-3, walk down 1-3
  row 3: walk up-right 1-3, walk down-right 1-3
  row 4: attack right 1-3, attack up 1-3, attack down 1-3"""
import math,pathlib
from PIL import Image,ImageDraw,ImageFont
ROOT=pathlib.Path(__file__).resolve().parent.parent;OUT=ROOT/'art'
CELL,COLS,ROWS=48,9,4
CELLS=[ # (column, row, label, arrow direction in degrees or None)
  (0,0,'IDLE',None),(1,0,'DAMAGED',None),(2,0,'DEATH',None)]
for name,col0,row,ang in [('WALK',0,1,0),('WALK',3,1,-90),('WALK',6,1,90),('WALK',0,2,-45),('WALK',3,2,45),
                          ('ATTACK',0,3,0),('ATTACK',3,3,-90),('ATTACK',6,3,90)]:
    for k in range(3):CELLS.append((col0+k,row,f'{name} {k+1}',ang))
DIRNAME={0:'right',-90:'up',90:'down',-45:'up-right',45:'down-right'}
HITBOX=11 # the character's body radius in the game, in pixels
# actual size: faint guides an artist can keep as a hidden layer
im=Image.new('RGBA',(CELL*COLS,CELL*ROWS),(0,0,0,0));d=ImageDraw.Draw(im)
for c,r,_,_ in CELLS:
    x,y=c*CELL,r*CELL
    d.rectangle([x,y,x+CELL-1,y+CELL-1],outline=(120,120,140,90))
    d.ellipse([x+24-HITBOX,y+24-HITBOX,x+24+HITBOX,y+24+HITBOX],outline=(240,163,58,70))
    d.point([(x+24,y+24)],fill=(240,163,58,160))
OUT.mkdir(exist_ok=True);im.save(OUT/'sprite-template.png')
# 4x labelled reference
S=4;g=Image.new('RGBA',(CELL*COLS*S,CELL*ROWS*S),(24,30,33,255));d=ImageDraw.Draw(g)
font=ImageFont.truetype(str(ROOT.parent/'ChakraPetch-SemiBold.ttf'),14);small=ImageFont.truetype(str(ROOT.parent/'ChakraPetch-SemiBold.ttf'),11)
used={(c,r) for c,r,_,_ in CELLS}
for r in range(ROWS):
    for c in range(COLS):
        x,y=c*CELL*S,r*CELL*S
        if (c,r) not in used:
            d.rectangle([x,y,x+CELL*S-1,y+CELL*S-1],fill=(16,20,22,255));continue
        d.rectangle([x,y,x+CELL*S-1,y+CELL*S-1],outline=(90,100,110,255))
for c,r,label,ang in CELLS:
    x,y=c*CELL*S,r*CELL*S;cx,cy=x+24*S,y+24*S
    d.ellipse([cx-HITBOX*S,cy-HITBOX*S,cx+HITBOX*S,cy+HITBOX*S],outline=(240,163,58,255),width=2)
    d.line([cx-6,cy,cx+6,cy],fill=(240,163,58,255));d.line([cx,cy-6,cx,cy+6],fill=(240,163,58,255))
    d.text((x+6,y+5),label,font=font,fill=(231,238,233,255))
    if ang is not None:
        d.text((x+6,y+23),DIRNAME[ang],font=small,fill=(212,195,255,255))
        a=math.radians(ang);L=30*S//4*3;ex,ey=cx+math.cos(a)*L,cy+math.sin(a)*L
        d.line([cx,cy,ex,ey],fill=(212,195,255,255),width=3)
        for s in (-1,1):
            b=a+math.pi+s*0.5;d.line([ex,ey,ex+math.cos(b)*12,ey+math.sin(b)*12],fill=(212,195,255,255),width=3)
note=['CRYSTAL ECHOES CHARACTER SHEET: 432 x 192 PNG, transparent background, 48 x 48 cells',
      'Art faces right. The game mirrors it for left (walk left, walk up-left, attack left...).',
      'Orange circle = the body hitbox (22 px across). Its centre = where the character stands in the arena.',
      'Weapons, capes and effects can go outside the circle, but stay inside the cell.',
      'Save as sprites/<character>.png: ninja, ranger, ghost, sprinter, trapper, frost, ben, time, sniper.']
for i,line in enumerate(note):d.text((3*CELL*S+16,16+i*30),line,font=font if i==0 else small,fill=(231,238,233,255) if i==0 else (170,185,182,255))
g.save(OUT/'sprite-template-guide.png')
print('wrote',OUT/'sprite-template.png',OUT/'sprite-template-guide.png')
