const API=""; // bir xil server
const T0=Date.now();
const tg=window.Telegram?.WebApp;tg?.ready();tg?.expand();
const $=s=>document.querySelector(s);
const S={u:{balance:0,spent:0,ref:"",refs:0,bonus:0},cat:{games:[],bot:"",support:""},tab:"games",view:"menu",game:null,sel:null,pid:"",region:"GLOBAL",hist:{orders:[],fin:[]},htab:"orders"};
async function api(p,b){try{const r=await fetch(API+p,{method:b?"POST":"GET",headers:{"Content-Type":"application/json","X-Init":tg?.initData||""},body:b?JSON.stringify(b):undefined});return await r.json()}catch(e){return null}}
const fmt=n=>(+n).toLocaleString("ru",{maximumFractionDigits:2});
const go=async v=>{S.view=v;if(v=="hist"){const r=await api("/api/history");if(r)S.hist=r}render();scrollTo(0,0)};
const NAV=[["menu","grid","menu"],["hist","hist","history"],["friends","users","friends"],["set","user","settings"]];
async function init(){
  await setLang(localStorage.getItem("lang")||"ru");
  const [me,cat]=await Promise.all([api("/api/me"),api("/api/catalog")]);
  if(me&&!me.error){S.u=me;if(me.lang&&me.lang!==LANG)await setLang(me.lang)}
  if(cat)S.cat=cat;
  if(localStorage.getItem("light"))document.body.classList.add("light");
  render();if(new URLSearchParams(location.search).get("go")=="hist")go("hist");setTimeout(()=>$("#splash").classList.add("hide"),Math.max(0,3000-(Date.now()-T0)))}
function render(){
  const v=S.view,m={menu,game,topup,meth,hist,friends,set,rev,top:topv,pay:payv},sub=["game","topup","meth","pay","rev"].includes(v);
  $("#app").innerHTML=m[v]();
  $("#nav").innerHTML=NAV.map(([k,i,n])=>`<a class="${v==k||(k=="menu"&&sub)||(k=="friends"&&v=="top")?"on":""}" onclick="go('${k}')">${I(i)}<span>${t(n)}</span></a>`).join("");
  if(tg)tg.BackButton[(sub||v=="top")?"show":"hide"]()}
tg?.BackButton.onClick(()=>go(S.view=="top"?"friends":"menu"));
const gi=g=>`<img class="gimg" src="/${g.id}.png?v=3" onerror="this.style.display='none'">`;
function menu(){const u=S.u,tgu=tg?.initDataUnsafe?.user||{};
  const games=S.cat.games.map(g=>`<div class="game" onclick="openGame('${g.id}')"><i style="background:${g.color}">${gi(g)}${g.icon}</i>${g.name}</div>`).join("");
  const gifts=(S.cat.gifts||[]).map(g=>`<div class="li"><div><b>${g.name}</b><br><small style="color:var(--mut)">${g.sub}</small></div>›</div>`).join("");
  const ai=(S.cat.ai||[]).map(g=>`<div class="pk"><b>${g.name}</b><span>${g.price} c.</span></div>`).join("");
  const body=S.tab=="games"?`<div class="grid3">${games}</div>`:S.tab=="gift"?`<div class="card">${gifts}</div>`:`<div class="grid3" style="grid-template-columns:1fr 1fr">${ai}</div>`;
  return `<div class="top"><div class="av">${tgu.photo_url?`<img src="${tgu.photo_url}">`:(tgu.first_name||"?")[0]}</div><div><b>${tgu.first_name||""}</b><br><small style="color:var(--mut)">${tgu.username?"@"+tgu.username:""}</small></div></div>
  <div class="bal"><small>${t("balance")}</small><h2>${fmt(u.balance)} <span>${t("cur")}</span></h2>
  <div class="row3"><div class="glass" onclick="go('topup')">💳<br>${t("topup")}</div><div class="glass" onclick="alert(t('nopromo'))">🎟<br>${t("bonus")}</div><div class="glass" onclick="tg&&tg.openTelegramLink('https://t.me/'+S.cat.support)">💬<br>${t("support")}</div></div></div>
  <div class="card" style="display:flex;align-items:center;gap:14px;padding:16px 18px" onclick="openReviews()"><div class="av" style="background:#3a3320;border-radius:14px;font-size:26px">⭐</div><div style="flex:1"><b style="font-size:24px">${(u.rating&&u.rating.count)?u.rating.avg.toFixed(1):"—"}</b> <span style="color:#facc15">★★★★★</span> <small style="color:var(--mut)">· ${(u.rating&&u.rating.count)||0} ${t("ratings_n")}</small></div><span style="color:var(--mut)">›</span></div>
  <div class="seg"><a class="${S.tab=="games"?"on":""}" onclick="S.tab='games';render()">${t("games")}</a><a class="${S.tab=="gift"?"on":""}" onclick="S.tab='gift';render()">Gift Code</a><a class="${S.tab=="ai"?"on":""}" onclick="S.tab='ai';render()">🤖 AI</a></div>${body}`}
function openGame(id){S.game=S.cat.games.find(g=>g.id==id);S.sel=null;S.pid="";S.checked=false;S.ptab=Object.keys(S.game.tabs)[0];go("game")}
function game(){const g=S.game;if(!g)return"";
  const tabs=Object.keys(g.tabs),items=g.tabs[S.ptab]||[];
  const regs=g.regions?`<div class="card"><div class="lbl">${t("region")}</div><div class="reg">${g.regions.map(r=>`<a class="${S.region==r?"on":""}" onclick="S.region='${r}';render()">${r}</a>`).join("")}</div></div>`:"";
  return `<div class="card top" style="margin:0 0 14px"><div class="av" style="background:${g.color};border-radius:14px;position:relative">${gi(g)}${g.icon}</div><div><b>${g.name}</b><br><small style="color:var(--mut)">${g.sub}</small></div></div>
  <div class="card"><div class="lbl">${t("playerid")}</div>${S.checked?`<div class="li" style="padding:6px 0"><b class="ok">✓ ${S.pid}</b><a onclick="S.checked=false;render()" style="color:var(--mut)">${t("change")}</a></div>`:`<div class="flex"><input id="pid" inputmode="numeric" placeholder="${t("enterid")}" value="${S.pid}"><button class="btn" style="width:auto;padding:0 18px" onclick="chk()">${t("check")}</button></div>`}</div>
  ${regs}<div class="lbl">${t("pick")}</div><div class="seg">${tabs.map(k=>`<a class="${S.ptab==k?"on":""}" onclick="S.ptab='${k}';S.sel=null;render()">${k}</a>`).join("")}</div>
  <div class="grid3" style="grid-template-columns:1fr 1fr">${items.map(i=>`<div class="pk ${S.sel==i.id?"on":""}" onclick="S.sel='${i.id}';render()">${i.off?`<em>-${i.off}%</em>`:""}<b>${i.name}</b><span>${i.price} ${t("cur")}</span></div>`).join("")}</div>
  <div class="buy"><button class="btn" ${S.sel&&S.checked?"":"disabled"} onclick="buy()">${t("choose")}</button></div>`}
function chk(){const v=$("#pid").value.trim();if(!/^\d{5,14}$/.test(v)){S.pid=v;return alert("ID?")}S.pid=v;S.checked=true;render()}
async function buy(){const r=await api("/api/order",{game:S.game.id,item:S.sel,pid:S.pid,region:S.region});
  if(r?.error=="funds"){alert(t("nofunds"));return go("topup")}
  if(r?.ok){S.u.balance=r.balance;alert(t("ordered"));go("hist")}else alert(t("err"))}
const CPY='<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#8b7bff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-left:6px"><rect x="9" y="9" width="12" height="12" rx="2.5"/><path d="M5 15V6a2 2 0 0 1 2-2h9"/></svg>';
const pi=id=>`<img class="gimg" src="/${id}.png?v=6" onerror="this.style.display='none'">`;
function modal(title,body,btn,cb,icon,bg){const o=document.createElement("div");o.style.cssText="position:fixed;inset:0;background:rgba(0,0,0,.78);z-index:30;display:flex;align-items:center;justify-content:center;padding:20px";
 const ic=icon||'<svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#22c993" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>';
 o.innerHTML=`<div style="background:var(--card);border:1px solid var(--line);border-radius:34px;padding:42px 28px 28px;width:100%;max-width:460px;text-align:center"><div style="width:124px;height:124px;border-radius:50%;background:${bg||"#22c99322"};display:grid;place-items:center;margin:0 auto 26px">${ic}</div><h2 style="font-size:28px;line-height:1.2;margin-bottom:14px">${title}</h2><p style="color:var(--mut);font-size:18px;line-height:1.5;margin-bottom:30px">${body}</p><button class="btn" style="padding:20px;font-size:19px">${btn}</button></div>`;
 o.querySelector("button").onclick=()=>{o.remove();cb&&cb()};document.body.appendChild(o)}
const rate=()=>S.cat.rate||0.108;
function toast(m){const d=document.createElement("div");d.textContent=m;d.style.cssText="position:fixed;top:70px;left:50%;transform:translateX(-50%);background:#22c993;color:#fff;padding:10px 18px;border-radius:14px;z-index:20;font-weight:700";document.body.appendChild(d);setTimeout(()=>d.remove(),1500)}
function cp(v){navigator.clipboard?.writeText(String(v).replace(/\s/g,""));toast(t("copied"))}
function topup(){const a=S.amt||"",R=rate();
  return `<h1 style="margin:10px 0 20px">${t("topup")}</h1><div class="lbl">${t("amount")}</div>
  <div class="grid3">${[10,20,50,100,200,500].map(x=>`<div class="pk" style="text-align:center" onclick="setAmt(${x})"><b>${x} ${t("cur")}</b></div>`).join("")}</div>
  <div class="card" style="margin-top:14px;padding:0;overflow:hidden"><div class="flex" style="gap:0"><div style="flex:1;display:flex;align-items:center;padding:6px 14px"><input id="amS" type="number" inputmode="decimal" placeholder="0" value="${a}" oninput="fromS()" style="border:0;background:none;padding:10px 0"><small style="color:var(--mut);font-weight:700">${t("cur")}</small></div><div style="width:1px;background:var(--line)"></div><div style="flex:1;display:flex;align-items:center;padding:6px 14px"><input id="amR" type="number" inputmode="decimal" placeholder="0" value="${a?Math.round(a/R):""}" oninput="fromR()" style="border:0;background:none;padding:10px 0"><small style="color:var(--mut);font-weight:700">₽</small></div></div>
  <div style="text-align:center;padding:10px;background:var(--card2);color:var(--mut);font-size:12px;font-weight:700">1 ₽ = ${R} ${t("cur")}</div></div>
  <button class="btn" onclick="toMeth()">${t("continue")} →</button>`}
function setAmt(x){S.amt=x;$("#amS").value=x;$("#amR").value=Math.round(x/rate())}
function fromS(){const v=+$("#amS").value;S.amt=v;$("#amR").value=v?Math.round(v/rate()):""}
function fromR(){const v=+$("#amR").value;S.amt=v?Math.round(v*rate()*100)/100:0;$("#amS").value=S.amt||""}
function toMeth(){if(!(S.amt>=10))return alert(t("min")+" 10 "+t("cur"));go("meth")}
function meth(){const rows=(S.cat.pay||[]).map(m=>{const amt=m.cur=="RUB"?Math.round(S.amt/rate())+" ₽":fmt(S.amt)+" "+t("cur");
  return `<div class="card" style="display:flex;justify-content:space-between;align-items:center;padding:14px 16px" onclick="pickM('${m.id}')"><div class="flex" style="align-items:center"><div class="av" style="background:${m.color};border-radius:14px;position:relative">${pi(m.id)}${m.icon}</div><div><b>${m.name}</b><br><small style="color:var(--mut)">${t(m.type=="card"?"bycard":"byphone")}</small></div></div><div style="text-align:right"><b style="color:#8b7bff">${amt}</b> ›</div></div>`}).join("");
  return `<a style="color:#8b7bff;font-weight:600" onclick="go('topup')">‹ ${t("changeamt")}</a><div class="lbl" style="margin-top:18px">${t("paymethod")}</div>${rows||`<p style="color:var(--mut)">—</p>`}`}
async function pickM(id){const r=await api("/api/topup",{amount:S.amt,method:id});if(r?.ok){S.pay=r;S.file=null;go("pay")}else alert(t("err"))}
function payv(){const p=S.pay||{};
  return `<a style="color:#8b7bff;font-weight:600" onclick="go('meth')">‹ ${t("changemeth")}</a>
  <div class="card" style="margin-top:14px;text-align:center"><div class="lbl">${t("payto")}</div><div class="av" style="background:${p.color};border-radius:22px;width:96px;height:96px;margin:6px auto 14px;font-size:30px;position:relative">${pi(p.method)}${p.icon}</div>
  <h1 onclick="cp(S.pay.pay)" style="font-size:40px">${p.pay} <span style="color:#8b7bff;font-size:20px">${p.cur=="RUB"?"₽":t("cur")}</span> ${CPY}</h1><small style="color:var(--mut)">${t("tapcopy")}</small>
  <div class="card" style="margin:16px 0 0;text-align:left;background:var(--bg);display:flex;justify-content:space-between;align-items:center"><div><div class="lbl" style="margin:0 0 6px">${t(p.type=="card"?"cardno":"phoneno")}</div><b style="font-size:20px">${p.value}</b><br><small style="color:var(--mut)">${p.holder}</small></div><div class="av" style="background:var(--card2);border-radius:50%" onclick="cp(S.pay.value)">${CPY}</div></div></div>
  <div style="text-align:center;color:var(--mut);margin:18px 0 10px">— ${t("afterpay")} —</div>
  <div class="card"><b>${t("uploadrc")}</b><label style="display:block;margin-top:14px;border:2px dashed var(--line);border-radius:18px;padding:26px;text-align:center;color:var(--mut)"><input type="file" accept="image/jpeg,image/png" style="display:none" onchange="pickF(this)">${S.file?`<img src="${S.prev}" style="max-width:100%;max-height:260px;border-radius:12px;display:block;margin:0 auto 10px"><small>✓ ${t("tapchange")}</small>`:`📷<br><b>${t("photo")}</b><br><small>JPG, PNG — 5MB</small>`}</label></div>
  <button class="btn" ${S.file?"":"disabled"} onclick="sendRc()">✅ ${t("sendconfirm")}</button>`}
function pickF(el){const f=el.files[0];if(!f)return;if(f.size>5*1024*1024)return alert("5MB");if(S.prev)URL.revokeObjectURL(S.prev);S.prev=URL.createObjectURL(f);S.file=f;render()}
function toJpeg(f){return new Promise((ok,no)=>{const im=new Image();im.onload=()=>{const k=Math.min(1,1280/Math.max(im.width,im.height)),c=document.createElement("canvas");c.width=im.width*k;c.height=im.height*k;c.getContext("2d").drawImage(im,0,0,c.width,c.height);ok(c.toDataURL("image/jpeg",.8))};im.onerror=no;im.src=URL.createObjectURL(f)})}
async function sendRc(){const b=document.querySelector(".btn");b.disabled=true;
  try{const img=await toJpeg(S.file);const r=await api("/api/receipt",{amount:S.pay.amount,method:S.pay.method,image:img});
    if(r?.ok){modal(t("rcpt_title"),t("rcpt_body"),t("gotit"),()=>{S.file=null;S.amt=0;go("menu")},'<span style="font-size:68px;line-height:1">⏳</span>',"#f59e0b24")}else{alert(t("err"));b.disabled=false}}catch(e){alert(t("err"));b.disabled=false}}
const esc=s=>String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
async function openReviews(){const r=await api("/api/reviews");if(r&&r.items)S.rv=r;S.rf={s:0,g:"",o:"new"};go("rev")}
function setRf(k,v){S.rf[k]=v;render()}
function rev(){const R=S.rv||{items:[],dist:{},count:0,avg:0},f=S.rf||{s:0,g:"",o:"new"},d=R.dist||{};
  const bars=[5,4,3,2,1].map(n=>{const p=R.count?Math.round((d[n]||0)*100/R.count):0;return `<div class="flex" style="align-items:center;gap:8px;margin:5px 0;font-size:13px;color:var(--mut)"><span style="width:10px">${n}</span><span style="color:#facc15">★</span><div style="flex:1;height:8px;border-radius:8px;background:var(--card2)"><div style="width:${p}%;height:100%;border-radius:8px;background:#facc15"></div></div><span style="width:36px;text-align:right">${p}%</span></div>`}).join("");
  let it=R.items.filter(x=>(!f.s||x.stars==f.s)&&(!f.g||x.game==f.g));
  if(f.o=="best")it=[...it].sort((a,b)=>b.stars-a.stars);if(f.o=="worst")it=[...it].sort((a,b)=>a.stars-b.stars);
  const games=[...new Set(R.items.map(x=>x.game).filter(Boolean))];
  const chip=(on,fn,txt)=>`<a class="${on?"on":""}" style="white-space:nowrap" onclick="${fn}">${txt}</a>`;
  const c1=[chip(!f.s,"setRf('s',0)",t("all")),...[5,4,3,2,1].map(n=>chip(f.s==n,`setRf('s',${n})`,`${n} ★ ${d[n]||0}`))].join("");
  const c2=games.map(g=>chip(f.g==g,`setRf('g','${f.g==g?"":g}')`,`🎮 ${esc(g.replace(/\s/g,""))} ${R.items.filter(x=>x.game==g).length}`)).join("");
  const cards=it.map(x=>`<div class="card"><div class="flex" style="align-items:center"><div class="av" style="background:hsl(${x.id*47%360} 55% 42%)">${esc((x.name||"?")[0].toUpperCase())}</div><div style="flex:1"><b>${esc(x.name)}</b><br><span style="color:#facc15;font-size:15px">${"★".repeat(x.stars)}<span style="color:var(--line)">${"★".repeat(5-x.stars)}</span></span> <small style="background:var(--card2);color:var(--mut);padding:2px 8px;border-radius:8px;font-weight:700">${esc(x.game.replace(/\s/g,""))}</small></div><small style="color:var(--mut)">${x.date}</small></div><div style="color:var(--mut);margin-top:10px">🛒 ${esc(x.item)}</div>${x.text?`<p style="margin-top:8px;line-height:1.4">${esc(x.text)}</p>`:""}${x.reply?`<div style="margin-top:10px;border-left:3px solid var(--pr);background:var(--bg);border-radius:10px;padding:10px 12px"><small style="color:#8b7bff;font-weight:700">🛡 Diavex Shop</small><br>${esc(x.reply)}</div>`:""}</div>`).join("");
  return `<h1 style="margin:10px 0 16px">${t("reviews")} <small style="color:var(--mut);font-size:16px">${R.count}</small></h1>
  <div class="card flex" style="align-items:center"><div style="text-align:center;padding:0 12px"><div style="font-size:52px;font-weight:800">${R.count?R.avg.toFixed(1):"—"}</div><div style="color:#facc15">★★★★★</div><small style="color:var(--mut)">${R.count} ${t("ratings_n")}</small></div><div style="flex:1">${bars}</div></div>
  <div class="reg" style="margin-bottom:10px">${c1}</div>${c2?`<div class="reg" style="margin-bottom:10px">${c2}</div>`:""}
  <div class="seg" style="margin-top:6px">${[["new","newest"],["best","best"],["worst","worst"]].map(([k,n])=>`<a class="${f.o==k?"on":""}" onclick="setRf('o','${k}')">${t(n)}</a>`).join("")}</div>
  ${cards||`<p style="color:var(--mut);text-align:center;margin-top:40px">${t("noreviews")}</p>`}`}
const P={
grid:'<rect x="4" y="4" width="6.5" height="6.5" rx="1.6"/><rect x="13.5" y="4" width="6.5" height="6.5" rx="1.6"/><rect x="4" y="13.5" width="6.5" height="6.5" rx="1.6"/><rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1.6"/>',
hist:'<path d="M3.5 12a8.5 8.5 0 1 0 2.6-6.1"/><path d="M3.5 4.5v4.8h4.8"/><path d="M12 7.5V12l3 1.8"/>',
users:'<circle cx="9" cy="8" r="3.4"/><path d="M2.8 20c0-3.5 2.8-5.8 6.2-5.8s6.2 2.3 6.2 5.8"/><circle cx="17.3" cy="9" r="2.6"/><path d="M17.8 14.3c2.4.3 3.9 2 3.9 4.7"/>',
user:'<circle cx="12" cy="8" r="4"/><path d="M4.5 21c0-4 3.4-6.5 7.5-6.5s7.5 2.5 7.5 6.5"/>',
globe:'<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.6 2.6 3.9 5.6 3.9 9S14.6 18.4 12 21c-2.6-2.6-3.9-5.6-3.9-9S9.4 5.6 12 3z"/>',
moon:'<path d="M20 14.5A8 8 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5z"/>',
bell:'<path d="M6 16.5V11a6 6 0 0 1 12 0v5.5l1.5 2h-15z"/><path d="M10 21h4"/>',
chat:'<path d="M20 12a8 8 0 0 1-11.6 7.1L4 20l1-4A8 8 0 1 1 20 12z"/>',
star:'<path d="M12 3.5l2.6 5.4 5.9.8-4.3 4.1 1 5.9-5.2-2.8-5.2 2.8 1-5.9-4.3-4.1 5.9-.8z"/>',
shield:'<path d="M12 3l7.5 3v5.5c0 4.6-3.1 8-7.5 9.5-4.4-1.5-7.5-4.9-7.5-9.5V6z"/><path d="M9 12l2.2 2.2L15.5 10"/>',
uplus:'<circle cx="10" cy="8" r="3.6"/><path d="M3.5 20c0-3.7 2.9-6 6.5-6 1.3 0 2.5.3 3.5.9"/><path d="M18 14v6M15 17h6"/>',
chev:'<path d="M9 6l6 6-6 6"/>',
up:'<path d="M12 19V5M5.5 11.5L12 5l6.5 6.5"/>',
down:'<path d="M12 5v14M5.5 12.5L12 19l6.5-6.5"/>',
refresh:'<path d="M20 11A8 8 0 0 0 5.6 6.8L4 8.5"/><path d="M4 4v4.5h4.5"/><path d="M4 13a8 8 0 0 0 14.4 4.2l1.6-1.7"/><path d="M20 20v-4.5h-4.5"/>',
tup:'<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
tdn:'<path d="M3 7l6 6 4-4 8 8"/><path d="M15 17h6v-6"/>',
copy:'<rect x="9" y="9" width="12" height="12" rx="2.5"/><path d="M5 15V6a2 2 0 0 1 2-2h9"/>',
back:'<path d="M15 6l-6 6 6 6"/>',
trophy:'<path d="M8 4h8v5a4 4 0 0 1-8 0z"/><path d="M8 6H5.5a1 1 0 0 0-1 1c0 2 1.5 3.5 3.5 4M16 6h2.5a1 1 0 0 1 1 1c0 2-1.500 3.5-3.5 4M12 13v4M8.5 20h7M10 17h4"/>',
wallet:'<path d="M4 7.5A2.5 2.5 0 0 1 6.5 5H18v3"/><rect x="3.5" y="8" width="17" height="11.5" rx="2.5"/><path d="M16 13.8h2.2"/>'
};
const I=(k,w=24)=>`<svg width="${w}" height="${w}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${P[k]}</svg>`;
const ini=s=>esc([...String(s||"?")][0]||"?");
const gid=n=>{const g=(S.cat.games||[]).find(x=>x.name==n);return g?g.id:""};
const ST={done:"st_done",pending:"st_wait",cancelled:"st_cancel"};
function setH(k,v){S[k]=v;render()}
async function refreshHist(){const r=await api("/api/history");if(r){S.hist=r;render()}}
function hist(){const H=S.hist,tab=S.htab||"orders";
  const head=`<div class="flex" style="align-items:center;justify-content:space-between;margin:10px 0 18px"><h1>${t("history")}</h1><div class="av" style="background:var(--card);border:1px solid var(--line);color:var(--tx)" onclick="refreshHist()">${I("refresh",22)}</div></div>
  <div class="seg" style="margin:0 0 16px"><a class="${tab=="orders"?"on":""}" onclick="setH('htab','orders')">${t("orders")}</a><a class="${tab=="fin"?"on":""}" onclick="setH('htab','fin')">${t("finance")}</a></div>`;
  const chips=(arr,key,cur)=>`<div class="reg chips" style="margin:0 0 14px">${arr.map(([k,n])=>`<a class="${cur==k?"on":""}" onclick="setH('${key}','${k}')">${t(n)}</a>`).join("")}</div>`;
  const none=`<p style="color:var(--mut);text-align:center;margin-top:40px">—</p>`;
  if(tab=="orders"){const f=S.hf||"all";
    const rows=H.orders.filter(x=>f=="all"||x.status==f).map(x=>{const g=gid(x.game);return `<div class="oc"><div class="oi">${g?pi(g):""}${x.game?ini(x.game):"🛒"}</div><div style="flex:1;min-width:0"><b class="tr">${esc(x.item||x.title)}</b><div class="sm">${esc(x.game||"")} · ${x.date}</div><div class="sm2">#${x.id}</div></div><div style="text-align:right;flex:none"><b>${fmt(x.price)} ${t("cur")}</b><br><span class="bd ${x.status}">${t(ST[x.status]||"st_wait")}</span></div></div>`}).join("");
    return head+chips([["all","st_all"],["done","st_done"],["pending","st_wait"],["cancelled","st_cancel"]],"hf",f)+(rows||none)}
  const inc=H.fin.filter(x=>x.amount>0).reduce((a,x)=>a+x.amount,0),exp=H.fin.filter(x=>x.amount<0).reduce((a,x)=>a-x.amount,0),f=S.ff||"all";
  const sum=(ic,col,lb,val,sg)=>`<div class="card" style="margin:0"><div class="sm" style="color:${col};display:flex;gap:6px;align-items:center;margin:0">${I(ic,18)}${t(lb)}</div><div style="font-size:28px;font-weight:800;color:${col};margin:10px 0 2px">${sg}${fmt(val)}</div><small style="color:var(--mut)">${t("cur")}</small></div>`;
  const rows=H.fin.filter(x=>f=="all"||(f=="in"?x.amount>0:x.amount<0)).map(x=>{const pos=x.amount>0,ti=x.title=="Top up"?t("fin_topup"):x.title=="Referral bonus"?t("fin_ref"):x.title;
    return `<div class="oc" style="border-left-width:1px"><div class="oi" style="background:${pos?"#10302a":"#321a1f"};color:${pos?"var(--ok)":"var(--bad)"}">${I(pos?"down":"up",24)}</div><div style="flex:1;min-width:0"><b class="tr">${esc(ti)}</b><div class="sm">${x.date}</div></div><b class="${pos?"ok":"bad"}" style="flex:none">${pos?"+":""}${fmt(x.amount)} ${t("cur")}</b></div>`}).join("");
  return head+`<div class="row3" style="grid-template-columns:1fr 1fr;margin-bottom:16px">${sum("tup","var(--ok)","total_income",inc,"+")}${sum("tdn","var(--bad)","total_expense",exp,"-")}</div>`+chips([["all","st_all"],["in","income"],["out","expense"]],"ff",f)+(rows||none)}
function friends(){const l=`https://t.me/${S.cat.bot}?start=${S.u.ref}`,c=(a,b)=>`<div class="card" style="text-align:center;margin:0"><h2>${a}</h2><small>${b}</small></div>`,tl=(ic,bg,col,k,fn)=>`<div class="card" style="margin:0;text-align:center" onclick="${fn}"><div class="ti" style="background:${bg};color:${col};margin:0 auto 8px">${I(ic,22)}</div><b style="font-size:14px">${t(k)}</b></div>`;
  return `<div class="hero"><small>+ ${t("bonus")}</small><h1>${t("invite")}</h1><p>${t("invsub")}</p></div>
  <div class="row3" style="margin-bottom:14px">${c(S.u.refs,t("invited"))}${c(S.u.buyers||0,t("buyers"))}${c(fmt(S.u.bonus),t("bonus"))}</div>
  <div class="row3" style="grid-template-columns:1fr 1fr;margin-bottom:14px">${tl("trophy","#33290f","#facc15","top_donors","openTop('donors')")}${tl("wallet","#12302a","#22c993","top_topups","openTop('topups')")}</div>
  <div class="card"><div class="lbl">${t("mylink")}</div><div class="card" style="background:var(--bg);color:var(--mut);word-break:break-all;padding:14px">${l}</div><div class="flex"><button class="btn" onclick="tg&&tg.openTelegramLink('https://t.me/share/url?url='+encodeURIComponent('${l}'))">${t("send")}</button><button class="btn" style="background:var(--card2)" onclick="navigator.clipboard.writeText('${l}')">${t("copy")}</button></div></div>
  <div class="card"><b>${t("rule")}</b> <span style="float:right;background:var(--ok);color:#fff;padding:4px 12px;border-radius:20px">2%</span></div>`}
const sup=()=>{if(tg&&S.cat.support)tg.openTelegramLink("https://t.me/"+S.cat.support)};
const note=()=>modal(t("notif"),t("notif_body"),t("gotit"));
const sec=()=>modal(t("security"),t("security_body"),t("gotit"));
function set(){const u=S.u,tu=tg?.initDataUnsafe?.user||{},nm=esc(((tu.first_name||"")+" "+(tu.last_name||"")).trim()||"—"),light=document.body.classList.contains("light");
  const av=tu.photo_url?`<img src="${esc(tu.photo_url)}" style="width:100%;height:100%;object-fit:cover">`:ini(tu.first_name);
  const mini=(lb,val,col)=>`<div style="flex:1;background:#ffffff0d;border:1px solid #ffffff14;border-radius:18px;padding:14px 16px"><small style="color:var(--mut);font-weight:700;letter-spacing:.06em">${t(lb).toUpperCase()}</small><div style="font-size:26px;font-weight:800;margin-top:6px;color:${col}">${fmt(val)} <small style="font-size:13px;color:var(--mut);font-weight:600">${t("cur")}</small></div></div>`;
  const rows=[["uplus","#12302a","#22c993","invite","go('friends')"],["bell","#33290f","#facc15","notif","note()"],["chat","#12303a","#38bdf8","support","sup()"],["star","#33290f","#facc15","reviews","openReviews()"],["shield","#1d2347","#8b7bff","security","sec()"]].map(([ic,bg,col,k,fn])=>`<div class="mr" onclick="${fn}"><div class="ti" style="background:${bg};color:${col}">${I(ic,22)}</div><b>${t(k)}</b><span class="chv">${I("chev",20)}</span></div>`).join("");
  return `<h1 style="margin:10px 0 16px">${t("profile")}</h1>
  <div class="card" style="background:linear-gradient(160deg,#171a33,#0d0f1c);padding:22px"><div class="flex" style="align-items:center;gap:16px;margin-bottom:18px"><div class="ring"><div>${av}</div></div><div style="min-width:0"><b style="font-size:20px">${nm}</b><br><small style="color:var(--mut)">${tu.username?"@"+esc(tu.username):""}</small><div class="chip" onclick="cp(${tu.id||0})">ID: ${tu.id||""} ${I("copy",14)}</div></div></div>
  <div class="flex" style="margin-bottom:16px">${mini("balance",u.balance,"var(--tx)")}${mini("spent",u.spent,"#f59a0b")}</div><button class="btn" style="background:#3b3399" onclick="go('topup')">${t("topup")}</button></div>
  <div class="card" style="padding:0"><div class="mr" style="border:0;padding-bottom:12px"><div class="ti" style="background:#12303a;color:#38bdf8">${I("globe",22)}</div><b>${t("lang")}</b></div><div style="padding:0 16px 16px"><div class="seg" style="margin:0">${[["uz","O'zbek"],["tg","Тоҷикӣ"],["ru","Русский"],["en","English"]].map(([k,n])=>`<a class="${LANG==k?"on":""}" onclick="chLang('${k}')">${n}</a>`).join("")}</div></div>
  <div class="mr" style="border-top:1px solid var(--line);border-bottom:0" onclick="document.body.classList.toggle('light');localStorage.setItem('light',document.body.classList.contains('light')?1:'');render()"><div class="ti" style="background:#1d2347;color:#8b7bff">${I("moon",22)}</div><b>${t("night")}</b><div class="sw ${light?"off":""}"></div></div></div>
  <div class="card" style="padding:0">${rows}</div>`}
async function openTop(k){S.tk=k;S.tp="week";await loadTop()}
async function loadTop(){const r=await api(`/api/top?kind=${S.tk}&period=${S.tp}`);S.top=(r&&r.items)||[];go("top")}
function topv(){const T=S.top||[],tp=S.tp||"week";
  const rows=T.map((x,i)=>{const m=["🥇","🥈","🥉"][i];return `<div class="rk ${i<3?"gold":""}"><span style="width:34px;text-align:center;font-size:${m?22:16}px;color:var(--mut);font-weight:700">${m||i+1}</span><div class="av" style="width:52px;height:52px;background:hsl(${((x.name||"?").charCodeAt(0)||0)*37%360} 55% 42%)">${ini(x.name)}</div><b class="tr" style="flex:1">${esc(x.name)}</b><b style="flex:none">${fmt(x.total)} TJS</b></div>`}).join("");
  return `<div class="flex" style="align-items:center;gap:14px;margin:8px 0 18px"><div class="av" style="background:var(--card);border:1px solid var(--line);color:var(--tx);width:48px;height:48px" onclick="go('friends')">${I("back",22)}</div><h1>${t(S.tk=="donors"?"top_donors":"top_topups")}</h1></div>
  <div class="seg" style="margin:0 0 16px">${[["week","week"],["month","month"],["all","alltime"]].map(([k,n])=>`<a class="${tp==k?"on":""}" onclick="S.tp='${k}';loadTop()">${t(n)}</a>`).join("")}</div>${rows||`<p style="color:var(--mut);text-align:center;margin-top:40px">${t("no_data")}</p>`}`}
async function chLang(l){await setLang(l);api("/api/lang",{lang:l});render()}
init();
