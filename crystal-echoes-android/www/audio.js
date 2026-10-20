/* ---------- Crystal Echoes audio ----------
   Every sound effect and both songs are synthesized live with the Web Audio API, so there are no audio files.
   window.CEAudio:
     sfx(name,{pan,vol})   play a sound effect (pan -1..1, vol 0..1)
     preview(characterKey) play that character's signature sound (draft cards)
     music(song,ducked)    'menu' (lo-fi hip hop) or 'game' (industrial drum and bass); safe to call every frame
     prefs / setPref(k,v)  music, sfx and muted switches, remembered on this device
   Browsers only allow sound after the first tap or key press, so nothing plays until then. */
(()=>{
const AC=window.AudioContext||window.webkitAudioContext;
const PREF_KEY='ce-audio';
const prefs={music:true,sfx:true,muted:false};
try{Object.assign(prefs,JSON.parse(localStorage.getItem(PREF_KEY)||'{}'));}catch(e){}
const savePrefs=()=>{try{localStorage.setItem(PREF_KEY,JSON.stringify(prefs));}catch(e){}};

const MUSIC_VOL=.3, SFX_VOL=.9, DUCK=.35; // music drops to 35% while paused
let ctx=null,out,musicBus,sfxBus,noiseBuf,player=null,wantSong=null,ducked=false;
const mtof=m=>440*Math.pow(2,(m-69)/12);

function build(c){ // the mixer: music and effects buses into a gentle limiter
  ctx=c;
  const comp=ctx.createDynamicsCompressor();
  comp.threshold.value=-12;comp.knee.value=10;comp.ratio.value=4;comp.attack.value=.004;comp.release.value=.2;
  out=ctx.createGain();out.connect(comp);comp.connect(ctx.destination);
  musicBus=ctx.createGain();musicBus.connect(out);
  sfxBus=ctx.createGain();sfxBus.connect(out);
  noiseBuf=ctx.createBuffer(1,ctx.sampleRate*2,ctx.sampleRate);
  const d=noiseBuf.getChannelData(0);for(let i=0;i<d.length;i++)d[i]=Math.random()*2-1;
}
function levels(instant){
  if(!ctx)return;
  const t=ctx.currentTime,k=instant?.001:.12;
  out.gain.setTargetAtTime(prefs.muted?0:1,t,k);
  musicBus.gain.setTargetAtTime(prefs.music?MUSIC_VOL*(ducked?DUCK:1):0,t,k);
  sfxBus.gain.setTargetAtTime(prefs.sfx?SFX_VOL:0,t,k);
}
function unlock(){ // called on every tap/key: creates the audio context the first time, resumes it after that
  if(!AC)return;
  if(!ctx){build(new AC());levels(true);}
  if(ctx.state!=='running'&&!document.hidden)ctx.resume().catch(()=>{});
  if(wantSong&&!player)startSong(wantSong);
}
['pointerdown','touchend','keydown'].forEach(t=>addEventListener(t,unlock,{capture:true,passive:true}));
document.addEventListener('visibilitychange',()=>{
  if(!ctx)return;
  if(document.hidden)ctx.suspend().catch(()=>{});else ctx.resume().catch(()=>{});
});

/* ---------- building blocks ---------- */
function env(g,t,a,vol,dur){ // quick attack, then an exponential fade to silence
  vol=Math.max(vol,1e-4);
  g.gain.setValueAtTime(1e-4,t);g.gain.exponentialRampToValueAtTime(vol,t+a);g.gain.exponentialRampToValueAtTime(1e-4,t+a+dur);
}
function tone(dest,t,{type='sine',f,f2,dur=.2,a=.005,vol=.2,detune=0}){
  const o=ctx.createOscillator(),g=ctx.createGain();
  o.type=type;o.frequency.setValueAtTime(f,t);if(f2)o.frequency.exponentialRampToValueAtTime(f2,t+a+dur);
  if(detune)o.detune.value=detune;
  env(g,t,a,vol,dur);o.connect(g);g.connect(dest);o.start(t);o.stop(t+a+dur+.05);
  return o;
}
function noise(dest,t,{type='bandpass',f=1000,f2,q=1,dur=.2,a=.003,vol=.3}){
  const s=ctx.createBufferSource(),fl=ctx.createBiquadFilter(),g=ctx.createGain();
  s.buffer=noiseBuf;s.loop=true;
  fl.type=type;fl.frequency.setValueAtTime(f,t);if(f2)fl.frequency.exponentialRampToValueAtTime(f2,t+a+dur);fl.Q.value=q;
  env(g,t,a,vol,dur);s.connect(fl);fl.connect(g);g.connect(dest);
  s.start(t,Math.random()*1.5);s.stop(t+a+dur+.05);
}
function vibrato(o,t,rate,cents,dur){
  const l=ctx.createOscillator(),g=ctx.createGain();
  l.frequency.value=rate;g.gain.value=cents;l.connect(g);g.connect(o.detune);l.start(t);l.stop(t+dur);
}
function lfoTo(lfoGain,o){ // shared LFO -> this oscillator's pitch, unhooked when the note ends
  lfoGain.connect(o.detune);o.onended=()=>{try{lfoGain.disconnect(o.detune);}catch(e){}};
}

/* ---------- sound effects ---------- */
const SFX={
  // Ninja: blade whoosh with a metallic ring
  slash(d,t){noise(d,t,{f:700,f2:5200,q:1.2,dur:.16,vol:.55});tone(d,t+.05,{f:2350,dur:.28,vol:.05});tone(d,t+.05,{f:3520,dur:.22,vol:.035});},
  // Ranger: bowstring creak while drawing, a ping at full draw, a twang and whoosh on release
  draw(d,t){tone(d,t,{type:'triangle',f:150,f2:230,dur:.3,a:.04,vol:.07});noise(d,t,{f:420,q:6,dur:.28,a:.05,vol:.12});},
  drawReady(d,t){tone(d,t,{f:1568,dur:.18,vol:.1});tone(d,t+.05,{f:2093,dur:.2,vol:.07});},
  arrow(d,t){tone(d,t,{type:'triangle',f:330,f2:180,dur:.22,vol:.32});noise(d,t,{type:'highpass',f:2500,dur:.12,vol:.25});},
  thud(d,t){tone(d,t,{f:160,f2:60,dur:.09,vol:.35});noise(d,t,{type:'lowpass',f:1200,dur:.06,vol:.3});},
  // Frostcaller: icy chimes on the throw, a crystalline crack on a freeze
  frostThrow(d,t){[1568,2093,2637,3136].forEach((f,i)=>tone(d,t+i*.03,{f,dur:.3,vol:.06}));noise(d,t,{type:'highpass',f:6000,dur:.28,vol:.12});},
  freeze(d,t){noise(d,t,{f:3200,q:2,dur:.08,vol:.45});tone(d,t,{type:'triangle',f:2600,f2:1700,dur:.4,vol:.08});[1319,1976,2637].forEach((f,i)=>tone(d,t+.04+i*.04,{f,dur:.5,vol:.05}));},
  iceHit(d,t){[2637,3520].forEach((f,i)=>tone(d,t+i*.025,{f,dur:.15,vol:.05}));noise(d,t,{type:'highpass',f:5000,dur:.06,vol:.15});},
  // Sniper: sharp crack, low body, and a long echo off the walls
  snipe(d,t){noise(d,t,{type:'highpass',f:900,dur:.06,vol:.9});tone(d,t,{f:180,f2:40,dur:.22,vol:.6});noise(d,t+.07,{f:700,q:.8,dur:.7,a:.02,vol:.12});},
  // Timekeeper: everything winds down like a stopped tape, with a tick-tock
  timeStop(d,t){
    tone(d,t,{f:880,f2:90,dur:.75,a:.02,vol:.16});tone(d,t,{type:'triangle',f:1320,f2:130,dur:.7,a:.02,vol:.06});
    for(const o of [.12,.42])tone(d,t+o,{type:'square',f:1900,dur:.02,vol:.05});
    noise(d,t,{type:'lowpass',f:3000,f2:200,dur:.7,a:.03,vol:.12});
  },
  // Sprinter: rising whoosh
  dash(d,t){noise(d,t,{f:500,f2:2800,q:1.5,dur:.2,vol:.45});tone(d,t,{f:300,f2:720,dur:.15,vol:.08});},
  // Trapper: mechanical click and a beep; two beeps when the mine arms; explosion
  minePlace(d,t){tone(d,t,{type:'square',f:900,dur:.03,vol:.06});tone(d,t+.01,{f:520,dur:.08,vol:.15});tone(d,t+.12,{f:1500,dur:.06,vol:.06});},
  mineArm(d,t){tone(d,t,{f:1760,dur:.05,vol:.07});tone(d,t+.09,{f:1760,dur:.05,vol:.07});},
  boom(d,t){tone(d,t,{f:130,f2:30,dur:.55,vol:.9});noise(d,t,{type:'lowpass',f:1600,f2:180,dur:.65,vol:.8});},
  // Ben Shieldon: metal clang when the shield blocks, a humming thump when he plants one
  block(d,t){[523,1247,1791,2489].forEach((f,i)=>tone(d,t,{f,dur:.5-i*.08,vol:.12-i*.02}));noise(d,t,{f:2500,q:1,dur:.04,vol:.35});},
  shieldPlant(d,t){tone(d,t,{f:95,f2:55,dur:.3,vol:.5});for(const f of [220,330,440])tone(d,t+.02,{f,dur:.8,a:.06,vol:.06});noise(d,t,{type:'highpass',f:4000,dur:.4,a:.05,vol:.06});},
  // Ghost: a falling wail when it haunts someone; a beating, eerie drone when it drops its spectres
  haunt(d,t){const o=tone(d,t,{f:740,f2:330,dur:.6,a:.05,vol:.13});vibrato(o,t,6,25,.7);tone(d,t,{type:'triangle',f:370,f2:165,dur:.6,a:.05,vol:.05});},
  spectreDrop(d,t){for(const f of [440,466])tone(d,t,{f,f2:f*.72,dur:.9,a:.12,vol:.09});},
  // shared game sounds
  ko(d,t){tone(d,t,{type:'square',f:620,f2:110,dur:.24,vol:.08});noise(d,t,{type:'lowpass',f:1400,dur:.12,vol:.35});},
  pickup(d,t){tone(d,t,{f:1319,dur:.18,vol:.12});tone(d,t+.06,{f:1976,dur:.25,vol:.12});},
  score(d,t){[1047,1319,1568,2093].forEach((f,i)=>tone(d,t+i*.07,{type:'triangle',f,dur:.35,vol:.14}));tone(d,t,{f:262,dur:.5,vol:.15});},
  drop(d,t){[1568,1175,880].forEach((f,i)=>tone(d,t+i*.06,{type:'triangle',f,dur:.2,vol:.1}));},
  tick(d,t){tone(d,t,{f:1250,dur:.05,vol:.18});noise(d,t,{type:'highpass',f:3000,dur:.02,vol:.1});},
  go(d,t){tone(d,t,{f:150,f2:50,dur:.25,vol:.5});tone(d,t,{type:'triangle',f:440,f2:880,dur:.25,vol:.1});[659,880,1319].forEach((f,i)=>tone(d,t+.1+i*.05,{f,dur:.35,vol:.06}));},
  turnEnd(d,t){[1,2.76,5.4].forEach((m,i)=>tone(d,t,{f:523*m,dur:1.4/(i+1),vol:.14/(i+1)}));},
  fanfare(d,t){[523,659,784,1047].forEach((f,i)=>tone(d,t+i*.12,{type:'triangle',f,dur:i===3?.9:.25,vol:.13}));for(const f of [523,659,784])tone(d,t+.48,{f,dur:.9,vol:.05});},
  runnerHome(d,t){[784,988,1319].forEach((f,i)=>tone(d,t+i*.05,{type:'square',f,dur:.12,vol:.05}));tone(d,t,{f:392,dur:.3,vol:.12});},
  click(d,t){tone(d,t,{f:880,dur:.035,vol:.06});}
};
const SIGNATURE={ninja:'slash',ranger:'arrow',ghost:'haunt',sprinter:'dash',trapper:'minePlace',frost:'frostThrow',ben:'block',time:'timeStop',sniper:'snipe'};
const lastPlayed={};
function sfx(name,o){
  if(!ctx||ctx.state!=='running'||!prefs.sfx||prefs.muted||!SFX[name])return;
  const t=ctx.currentTime;
  if(lastPlayed[name]>t-.035)return; // many echoes doing the same thing at once: play it once
  lastPlayed[name]=t;
  const g=ctx.createGain();g.gain.value=o&&o.vol!=null?o.vol:1;
  if(o&&o.pan&&ctx.createStereoPanner){const p=ctx.createStereoPanner();p.pan.value=Math.max(-1,Math.min(1,o.pan));g.connect(p);p.connect(sfxBus);}
  else g.connect(sfxBus);
  SFX[name](g,t+.005);
}

/* ---------- music ----------
   Both songs loop 8 bars.
   menu = lo-fi hip hop (76 BPM, swung, electric piano, vinyl crackle)
   game = industrial drum and bass (172 BPM, distorted two-step drums, metal clanks, growling reese bass) */
const PROG=[ // one chord per bar: bass root and a voicing (MIDI notes)
  {r:38,v:[53,57,60,64]}, // Dm9
  {r:43,v:[53,57,59,64]}, // G13
  {r:36,v:[52,55,59,62]}, // Cmaj9
  {r:45,v:[55,59,60,64]}, // Am9
  {r:38,v:[53,57,60,64]}, // Dm9
  {r:43,v:[53,57,59,64]}, // G13
  {r:40,v:[50,55,59,62]}, // Em7
  {r:45,v:[55,61,65,69]}  // A7(b13)
];
const MELODY=[ // [16th-note step within the 8 bars, MIDI note, length in steps]
  [0,76,3],[3,74,1],[4,72,2],[6,69,6],
  [18,67,2],[20,69,2],[22,72,4],[28,74,4],
  [32,76,6],[38,79,2],[40,76,4],[44,74,4],
  [48,72,8],[58,69,6],
  [64,76,3],[67,74,1],[68,72,2],[70,69,6],
  [82,67,2],[84,69,2],[86,72,2],[88,74,2],[90,76,6],
  [96,79,4],[100,76,4],[104,74,4],[108,71,4],
  [112,73,6],[118,76,4],[124,69,4]
];
const MEL_AT={};for(const [s,m,l] of MELODY)(MEL_AT[s]=MEL_AT[s]||[]).push([m,l]);

// drums
function kick(d,t,v){tone(d,t,{f:140,f2:42,dur:.32,a:.002,vol:v});tone(d,t,{type:'triangle',f:900,f2:200,dur:.015,vol:v*.15});}
function snare(d,t,v,soft){noise(d,t,{f:soft?1500:2200,q:soft?1.2:.6,dur:soft?.16:.2,vol:v});tone(d,t,{type:'triangle',f:200,f2:160,dur:.08,vol:v*.6});}
function hat(d,t,v,open){noise(d,t,{type:'highpass',f:7500,dur:open?.22:.04,vol:v});}
function crash(d,t,v){noise(d,t,{type:'highpass',f:4500,dur:1.3,vol:v});}

// lo-fi instruments
function epiano(p,t,m,dur,v){ // warm sine body, a soft octave, and a short bell-like tine
  const f=mtof(m);
  lfoTo(p.wob,tone(p.bus,t,{f,dur:dur+.4,a:.008,vol:v}));
  tone(p.bus,t,{type:'triangle',f:f*2,dur:dur*.5,vol:v*.15});
  tone(p.bus,t,{f:f*4.02,dur:.2,vol:v*.1});
}
function softLead(p,t,m,dur,v){ // breathy, flute-like melody
  const f=mtof(m);
  lfoTo(p.wob,tone(p.bus,t,{type:'triangle',f,dur:dur+.15,a:.04,vol:v}));
  tone(p.bus,t,{f:f*2,dur:dur*.6,a:.04,vol:v*.2});
}
function softBass(d,t,m,dur,v){tone(d,t,{f:mtof(m),dur,a:.012,vol:v});tone(d,t,{type:'triangle',f:mtof(m),dur:dur*.6,a:.012,vol:v*.25});}

// drum and bass instruments
function distCurve(k){const n=2048,c=new Float32Array(n);for(let i=0;i<n;i++){const x=i*2/n-1;c[i]=(1+k)*x/(1+k*Math.abs(x));}return c;}
function driveBus(dest,k,vol){ // waveshaper grit; returns the input
  const sh=ctx.createWaveShaper(),post=ctx.createGain();
  sh.curve=distCurve(k);sh.oversample='2x';post.gain.value=vol;sh.connect(post);post.connect(dest);return sh;
}
function gVoice(dest,t,f,detune,dur,v,rel,type){ // sustained oscillator note
  const o=ctx.createOscillator(),g=ctx.createGain();
  o.type=type||'sawtooth';o.frequency.value=f;o.detune.value=detune;
  g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(v,t+.004);g.gain.setValueAtTime(v,t+dur);g.gain.exponentialRampToValueAtTime(1e-4,t+dur+rel);
  o.connect(g);g.connect(dest);o.start(t);o.stop(t+dur+rel+.05);
  return o;
}
function dnbKick(d,t,v){tone(d,t,{f:190,f2:48,dur:.22,a:.001,vol:v});noise(d,t,{type:'highpass',f:3000,dur:.012,a:.001,vol:v*.4});}
function dnbSnare(d,t,v){noise(d,t,{f:1900,q:.7,dur:.17,a:.001,vol:v});tone(d,t,{type:'triangle',f:240,f2:170,dur:.07,vol:v*.7});noise(d,t,{type:'highpass',f:5000,dur:.08,vol:v*.35});}
function clank(d,t,v){ // industrial metal hit: clashing square partials and a ringing noise ping
  for(const [f,k] of [[317,1],[732,.7],[1183,.5],[1876,.35]])tone(d,t,{type:'square',f,dur:.09+.12*k,a:.001,vol:v*k*.25});
  noise(d,t,{f:2600,q:14,dur:.12,a:.001,vol:v*.9});
}
function reese(p,t,m,dur,v){ // two detuned saws through a moving low-pass, plus a clean sub
  for(const dt of [-14,14])gVoice(p.bass,t,mtof(m),dt,dur,v,.06);
  gVoice(p.g,t,mtof(m),0,dur,v*1.4,.06,'sine');
}
const DNB_BASS=[38,38,34,36,38,38,41,40]; // D D Bb C D D F E

const SONGS={
  menu:{bpm:76,swing:.28,vol:1.5,
    setup(p){
      p.bus=ctx.createBiquadFilter();p.bus.type='lowpass';p.bus.frequency.value=2600;p.bus.Q.value=.5;p.bus.connect(p.g); // muffled, like an old record
      p.lfo=ctx.createOscillator();p.lfo.frequency.value=.45;p.wob=ctx.createGain();p.wob.gain.value=9; // slow tape wobble
      p.lfo.connect(p.wob);p.lfo.start();
      const cr=ctx.createBufferSource(),bp=ctx.createBiquadFilter(),cg=ctx.createGain(); // vinyl hiss
      cr.buffer=noiseBuf;cr.loop=true;bp.type='bandpass';bp.frequency.value=5000;bp.Q.value=.6;cg.gain.value=.012;
      cr.connect(bp);bp.connect(cg);cg.connect(p.g);cr.start();
      p.stopAll=()=>{p.lfo.stop();cr.stop();};
    },
    play(p,t,bar,st){
      const c=PROG[bar],d=p.bus,sd=p.sd;
      if(st===0||st===10||(st===7&&bar%2))kick(d,t,.55);
      if(st===4||st===12)snare(d,t,.22,true);
      if(st%2===0)hat(d,t,st%4?.05:.08);else if(st===15)hat(d,t,.03);
      if(st===0)softBass(d,t,c.r,sd*7,.32);
      if(st===10)softBass(d,t,c.r+(bar%2?7:12),sd*4,.22);
      if(st===0)c.v.forEach((m,i)=>epiano(p,t+i*.012,m,sd*13,.07)); // a slight strum
      if(st===14&&bar%2===0)c.v.slice(1).forEach(m=>epiano(p,t,m,sd*3,.035));
      if(p.pass%3!==0)(MEL_AT[bar*16+st]||[]).forEach(([m,l])=>softLead(p,t,m,sd*l,.06)); // melody 2 times out of 3
      if(Math.random()<.08)noise(p.g,t+Math.random()*sd,{type:'highpass',f:2000,dur:.006,a:.001,vol:.04+Math.random()*.06}); // crackle pops
    }},
  game:{bpm:172,swing:0,vol:.6,
    setup(p){
      p.kit=driveBus(p.g,6,.55); // the whole drum kit runs through a little distortion
      const lp=ctx.createBiquadFilter();lp.type='lowpass';lp.frequency.value=420;lp.Q.value=6;
      p.lfo=ctx.createOscillator();p.lfo.frequency.value=172/60/2;const depth=ctx.createGain();depth.gain.value=280; // filter wobbles every 2 beats
      p.lfo.connect(depth);depth.connect(lp.frequency);p.lfo.start();
      p.bass=ctx.createGain();p.bass.connect(lp);lp.connect(driveBus(p.g,3,.5));
      p.stopAll=()=>p.lfo.stop();
    },
    play(p,t,bar,st){
      const sd=p.sd,k=p.kit;
      if(bar===7&&st>=8){if(st%2===0||st>=12)dnbSnare(k,t,.25+.03*(st-8));} // snare roll back to the top
      else{ // two-step: kick on 1 and the "and" of 3, snare on 2 and 4, ghost snares in odd bars
        if(st===0||st===10)dnbKick(k,t,.9);
        if(st===4||st===12)dnbSnare(k,t,.6);
        if(bar%2&&(st===7||st===9))dnbSnare(k,t,.12);
      }
      hat(k,t,st%4===2?.09:st%2?.03:.05,st===2&&bar%2===1);
      if((st===6&&bar%2===0)||(st===14&&bar%4===3))clank(k,t,.5);
      if(st===0&&bar%4===0)crash(k,t,.12);
      const r=DNB_BASS[bar];
      if(st===0)reese(p,t,r,sd*9,.12);
      if(st===10)reese(p,t,r,sd*5,.12);
    }}
};
const BARS=8,STEPS=BARS*16;
function newPlayer(name){
  const def=SONGS[name],g=ctx.createGain(),t=ctx.currentTime;
  g.gain.setValueAtTime(1e-4,t);g.gain.exponentialRampToValueAtTime(def.vol,t+.8);g.connect(musicBus);
  const p={name,def,g,step:0,pass:0,t:t+.08,sd:60/def.bpm/4};
  def.setup(p);return p;
}
function schedule(p,until){
  if(p.t<ctx.currentTime)p.t=ctx.currentTime+.03; // fell behind (slow device or tab was hidden): skip ahead instead of bursting
  while(p.t<until){
    const s=p.step%STEPS;
    p.def.play(p,p.t+(s%2?p.def.swing*p.sd:0),(s/16)|0,s%16);
    p.t+=p.sd;if(++p.step%STEPS===0)p.pass++;
  }
}
function startSong(name){
  if(player){
    const old=player,t=ctx.currentTime;player=null;
    clearInterval(old.timer);
    old.g.gain.cancelScheduledValues(t);old.g.gain.setTargetAtTime(0,t,.2); // fade out over about half a second
    setTimeout(()=>{old.stopAll();old.g.disconnect();},1500);
  }
  if(!name||!ctx)return;
  const p=newPlayer(name);
  p.timer=setInterval(()=>schedule(p,ctx.currentTime+.2),25);schedule(p,ctx.currentTime+.2);
  player=p;
}
function music(name,duck){
  if(!!duck!==ducked){ducked=!!duck;levels();}
  if(name===wantSong)return;
  wantSong=name;
  if(ctx)startSong(name);
}
function setPref(k,v){prefs[k]=v;savePrefs();levels();}

// Renders audio offline into a buffer (used to preview the songs and effects without a browser tab playing them).
async function render(seconds,{song,sfxAt}={}){
  if(!window.OfflineAudioContext)return null;
  const saved=[ctx,out,musicBus,sfxBus,noiseBuf];
  build(new OfflineAudioContext(2,Math.ceil(44100*seconds),44100));
  musicBus.gain.value=MUSIC_VOL;sfxBus.gain.value=SFX_VOL;
  if(song)schedule(newPlayer(song),seconds);
  for(const [time,name] of sfxAt||[]){const g=ctx.createGain();g.connect(sfxBus);SFX[name](g,time);}
  const buf=await ctx.startRendering();
  [ctx,out,musicBus,sfxBus,noiseBuf]=saved;
  return buf;
}

window.CEAudio={sfx,preview:k=>SIGNATURE[k]&&sfx(SIGNATURE[k]),music,prefs,setPref,unlock,render,SFX_NAMES:Object.keys(SFX)};
})();
