"""Build www/index.html (the phone version) from the desktop game file.

Usage: python3 tools/build_www.py path/to/crystal-echoes.html
The desktop file stays the source of truth for game rules; this script swaps
in the phone layout (full-screen landscape, floating joystick, bundled fonts).
"""
import sys, re, pathlib

src = pathlib.Path(sys.argv[1]).read_text()
root = pathlib.Path(__file__).resolve().parent.parent

css_start = src.index('<style>') + len('<style>')
css_end = src.index('</style>')
desktop_css = src[css_start:css_end]
script = src[src.index('<script>') + len('<script>'):src.index('</script>')]

def rep(text, a, b, count=1):
    assert a in text, 'missing: ' + a[:70]
    return text.replace(a, b, count)

# ---------- script patches ----------
# 1) touch: replace the fixed stick/button with a floating joystick (left half) + action zone (right half)
a = script.index("const stick=$('stick')")
b = script.index("['pointerup','pointercancel'].forEach(t=>$('abtn')")
b = script.index('\n', b) + 1
script = script[:a] + r"""/* ---------- touch: drag anywhere on the left half to move, touch the right half to act ---------- */
let touchHeld=false;
const tl=$('touchLayer'),ring=$('ring'),knob=$('knob'),tap=$('tap');
let moveId=null,actId=null,ox=0,oy=0;
function stickTo(x,y){
  const dx=x-ox,dy=y-oy,d=Math.hypot(dx,dy),m=Math.min(d,44);
  knob.style.transform=d?`translate(${dx/d*m}px,${dy/d*m}px)`:'';
  if(d<12){touchDir[0]=touchDir[1]=0;return;}
  const a=Math.round(Math.atan2(dy,dx)/(Math.PI/4))*Math.PI/4;
  touchDir[0]=Math.round(Math.cos(a));touchDir[1]=Math.round(Math.sin(a));
}
tl.addEventListener('pointerdown',ev=>{
  ev.preventDefault();try{tl.setPointerCapture(ev.pointerId);}catch(e){}
  if(ev.clientX<innerWidth/2){
    if(moveId!==null)return;
    moveId=ev.pointerId;ox=ev.clientX;oy=ev.clientY;
    ring.style.left=ox+'px';ring.style.top=oy+'px';ring.hidden=false;knob.style.transform='';
  }else{
    if(actId!==null)return;
    actId=ev.pointerId;touchHeld=true;if(state==='play')actQ[1]=true;
    tap.style.left=ev.clientX+'px';tap.style.top=ev.clientY+'px';tap.hidden=false;
  }
});
tl.addEventListener('pointermove',ev=>{if(ev.pointerId===moveId)stickTo(ev.clientX,ev.clientY);});
function touchEnd(ev){
  if(ev.pointerId===moveId){moveId=null;touchDir[0]=touchDir[1]=0;ring.hidden=true;}
  if(ev.pointerId===actId){actId=null;touchHeld=false;tap.hidden=true;}
}
tl.addEventListener('pointerup',touchEnd);tl.addEventListener('pointercancel',touchEnd);
function releaseTouch(){moveId=actId=null;touchHeld=false;touchDir[0]=touchDir[1]=0;ring.hidden=true;tap.hidden=true;}
"""+script[b:]
script = rep(script, "const showTouch=()=>$('touch').classList.toggle('on',state==='play'&&matchMedia('(pointer:coarse)').matches&&!cpuTurn());",
    "const showTouch=()=>{const on=state==='play'&&!cpuTurn();tl.hidden=!on;if(!on)releaseTouch();};")
# 2) no temporary reset button on phone (pause menu has Quit)
script = rep(script, "$('reset').onclick=showSetup; // temporary reset button\n", "")
# 3) setup screen gets a How to play button
script = rep(script, """    <button class="btn" id="go" type="button">Start round 1</button>
  </div>`);""", """    <div class="row"><button class="btn" id="go" type="button">Start round 1</button><button class="btn ghost" id="how" type="button">How to play</button></div>
  </div>`);
  $('how').onclick=showHowTo;""")
script = rep(script, "function showDraft(){", """function showHowTo(){
  showOv(`<div class="panel wide"><p class="eyebrow">How to play</p><h2>Carry crystals to the center ring.</h2>${$('rules').innerHTML}
    <button class="btn" id="back" type="button">Back</button></div>`);
  $('back').onclick=showSetup;
}
function showDraft(){""")
# 4) touch hint in the countdown
script = rep(script, "ctx.fillText(n?`${n} echo", "if(!cpuTurn()){ctx.fillStyle='#8a9d99';ctx.fillText('Left side: drag to move. Right side: touch to act (hold to draw the bow).',480,360);ctx.fillStyle='#c3d0cc';}\n    ctx.fillText(n?`${n} echo")
# 5) pause button + Android back button
script = rep(script, "showSetup();\nrequestAnimationFrame(frame);", """$('pauseBtn').onclick=()=>{if(state==='play')pause();else if(state==='paused')resume();};
const CapApp=window.Capacitor&&window.Capacitor.Plugins&&window.Capacitor.Plugins.App;
if(CapApp)CapApp.addListener('backButton',()=>{ // Android back: pause, resume, or leave from the setup screen
  if(state==='play')pause();else if(state==='paused')resume();else if(state==='setup')CapApp.exitApp();else showSetup();
});
showSetup();
requestAnimationFrame(frame);""")

# ---------- rules list (from the desktop guide) ----------
rules = src[src.index('<h2>Rules</h2>'):]
rules = rules[rules.index('<ul>'):rules.index('</ul>') + 5]
rules = rules.replace("pass the keyboard or phone", "pass the phone")

fonts = ''.join(f"@font-face{{font-family:'{fam}';src:url('fonts/{file}') format('truetype');font-weight:{w};font-display:swap}}\n"
    for fam, file, w in [('Chakra Petch','ChakraPetch-Medium.ttf',500),('Chakra Petch','ChakraPetch-SemiBold.ttf',600),('Chakra Petch','ChakraPetch-Bold.ttf',700),
                         ('Barlow','Barlow-Regular.ttf',400),('Barlow','Barlow-Medium.ttf',500),('Barlow','Barlow-SemiBold.ttf',600)])

mobile_css = r"""
/* ---------- phone layout ---------- */
html,body{height:100%;margin:0;overflow:hidden;overscroll-behavior:none;background:var(--bg);-webkit-user-select:none;user-select:none;-webkit-tap-highlight-color:transparent}
body{display:flex;align-items:center;justify-content:center;touch-action:none;font-size:14px}
.app{position:relative;display:flex;flex-direction:column;width:min(100vw,calc((100dvh - 34px)*960/576))}
.app .stage{width:100%;aspect-ratio:960/576;border:0;border-radius:0}
.hud{position:relative;z-index:4;height:34px;box-sizing:border-box;border:0;border-radius:0;background:var(--panel);padding:2px 8px;gap:6px}
.hud .score{font-size:18px}
.hud .who b{font-size:10px}.hud .who small{font-size:9px;display:block}
.hud .mid small{font-size:8px}.hud .timer{font-size:15px}.hud .pip{width:6px;height:6px}
.pausebtn{font:700 12px var(--display);background:transparent;color:var(--ink);border:1px solid var(--line);border-radius:4px;padding:2px 8px;margin-left:6px}
.ov{position:fixed;inset:0;z-index:5;padding:max(10px,env(safe-area-inset-top)) max(14px,env(safe-area-inset-right)) max(10px,env(safe-area-inset-bottom)) max(14px,env(safe-area-inset-left));touch-action:pan-y;-webkit-user-select:none}
.panel{gap:10px}.panel h2{font-size:21px}.panel p{font-size:13.5px}
.cards{grid-template-columns:repeat(3,1fr);gap:8px}
.card{padding:9px;gap:4px}.card p{font-size:12px;line-height:1.3}.card h3{font-size:15px}.card svg{width:26px;height:26px}
.stats{font-size:11px;gap:10px}
.tiers{grid-template-columns:repeat(3,1fr)}.tier span:last-child{font-size:12px}
.rules{margin:0;padding-left:18px;display:grid;gap:6px;color:#c3d0cc;font-size:13px;max-width:none}
.touchlayer{position:fixed;inset:0;z-index:3;touch-action:none}
.ring{position:fixed;width:104px;height:104px;margin:-52px 0 0 -52px;border-radius:50%;border:2px solid rgba(231,238,233,.35);background:rgba(231,238,233,.06);pointer-events:none}
.ring .knob{position:absolute;left:50%;top:50%;width:44px;height:44px;margin:-22px 0 0 -22px;border-radius:50%;background:rgba(240,163,58,.8)}
.tap{position:fixed;width:70px;height:70px;margin:-35px 0 0 -35px;border-radius:50%;background:rgba(212,195,255,.28);border:2px solid rgba(212,195,255,.6);pointer-events:none}
.rotate{position:fixed;inset:0;z-index:9;display:none;align-items:center;justify-content:center;text-align:center;padding:24px;background:var(--bg);font:600 18px var(--display);letter-spacing:.06em}
@media (orientation:portrait){.rotate{display:flex}}
@media (max-width:760px){.stage.has-ov{aspect-ratio:auto}.stage.has-ov canvas{display:block}.cards{grid-template-columns:repeat(3,1fr)}.tiers{grid-template-columns:repeat(3,1fr)}}
"""

markup = """<div class="app">
  <div class="hud" aria-live="off">
    <div class="side">
      <span class="score p1c" id="s1">0</span>
      <span class="who"><b class="p1c">Amber</b><small id="c1">Not picked</small></span>
    </div>
    <div class="mid">
      <small id="rl">Setup</small>
      <span class="timer" id="tm">15.0</span>
      <span class="pips" id="pips"></span>
    </div>
    <div class="side r">
      <span class="who"><b class="p2c" id="n2">Cobalt</b><small id="c2">Not picked</small></span>
      <span class="score p2c" id="s2">0</span>
      <button type="button" class="pausebtn" id="pauseBtn" aria-label="Pause">II</button>
    </div>
  </div>
  <div class="stage" id="stage">
    <canvas id="cv" width="960" height="576" aria-label="Game arena"></canvas>
  </div>
</div>
<div class="ov" id="ov"></div>
<div class="touchlayer" id="touchLayer" hidden>
  <div class="ring" id="ring" hidden><div class="knob" id="knob"></div></div>
  <div class="tap" id="tap" hidden></div>
</div>
<div id="rules" hidden>""" + rules.replace('<ul>', '<ul class="rules">', 1) + """</div>
<div class="rotate">Turn your phone sideways to play.</div>
"""

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">
<meta name="theme-color" content="#0d1315">
<title>Crystal Echoes</title>
<style>
{fonts}{desktop_css}{mobile_css}</style>
</head>
<body>
{markup}<script>{script}</script>
</body>
</html>
"""
out = root / 'www' / 'index.html'
out.write_text(page)
print('wrote', out, len(page), 'bytes')
