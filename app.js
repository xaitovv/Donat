const API=""; // bir xil server
const T0=Date.now();
const tg=window.Telegram?.WebApp;tg?.ready();tg?.expand();
const $=s=>document.querySelector(s);
const S={u:{balance:0,spent:0,ref:"",refs:0,bonus:0},cat:{games:[],bot:"",support:""},tab:"games",view:"menu",game:null,sel:null,pid:"",region:"GLOBAL",hist:{orders:[],fin:[]},htab:"orders"};
async function api(p,b){try{const r=await fetch(API+p,{method:b?"POST":"GET",headers:{"Content-Type":"application/json","X-Init":tg?.initData||""},body:b?JSON.stringify(b):undefined});return await r.json()}catch(e){return null}}
const fmt=n=>(+n).toLocaleString("ru",{maximumFractionDigits:2});
const go=async v=>{S.view=v;if(v=="hist"){const r=await api("/api/history");if(r)S.hist=r}render();scrollTo(0,0)};
const NAV=[["menu","▦","menu"],["hist","🕘","history"],["friends","👥","friends"],["set","👤","settings"]];
async function init(){
  await setLang(localStorage.getItem("lang")||"ru");
  const [me,cat]=await Promise.all([api("/api/me"),api("/api/catalog")]);
  if(me&&!me.error){S.u=me;if(me.lang&&me.lang!==LANG)await setLang(me.lang)}
  if(cat)S.cat=cat;
  if(localStorage.getItem("light"))document.body.classList.add("light");
  render();if(new URLSearchParams(location.search).get("go")=="hist")go("hist");setTimeout(()=>$("#splash").classList.add("hide"),Math.max(0,3000-(Date.now()-T0)))}
function render(){
  const v=S.view,m={menu,game,topup,meth,hist,friends,set,rev,pay:payv},sub=["game","topup","meth","pay","rev"].includes(v);
  $("#app").innerHTML=m[v]();
  $("#nav").innerHTML=NAV.map(([k,i,n])=>`<a class="${v==k||(k=="menu"&&sub)?"on":""}" onclick="go('${k}')"><i>${i}</i>${t(n)}</a>`).join("");
  if(tg)tg.BackButton[sub?"show":"hide"]()}
tg?.BackButton.onClick(()=>go("menu"));
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
function modal(title,body,btn,cb){const o=document.createElement("div");o.style.cssText="position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:30;display:flex;align-items:center;justify-content:center;padding:24px";
 o.innerHTML=`<div style="background:var(--card);border:1px solid var(--line);border-radius:28px;padding:30px 24px 24px;width:100%;max-width:380px;text-align:center"><div style="width:84px;height:84px;border-radius:50%;background:#22c99322;display:grid;place-items:center;margin:0 auto 18px"><svg width="46" height="46" viewBox="0 0 24 24" fill="none" stroke="#22c993" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></div><h2 style="font-size:24px;margin-bottom:10px">${title}</h2><p style="color:var(--mut);font-size:16px;line-height:1.45;margin-bottom:22px">${body}</p><button class="btn">${btn}</button></div>`;
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
  try{const img=await toJpeg(S.file);const r=await api("/api/receipt",{id:S.pay.id,method:S.pay.method,image:img});
    if(r?.ok){modal(t("rcpt_title"),t("rcpt_body"),t("gotit"),()=>{S.file=null;S.amt=0;go("menu")})}else{alert(t("err"));b.disabled=false}}catch(e){alert(t("err"));b.disabled=false}}
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
function hist(){const H=S.hist;
  const o=S.htab=="orders"?H.orders.map(x=>`<div class="card li"><div><b>${x.title}</b><br><small style="color:var(--mut)">#${x.id} · ${x.date}</small></div><div style="text-align:right"><b>${x.price} ${t("cur")}</b><br><small class="ok">${x.status}</small></div></div>`).join(""):H.fin.map(x=>`<div class="card li"><div><b>${x.title}</b><br><small style="color:var(--mut)">${x.date}</small></div><b class="${x.amount>0?"ok":"bad"}">${x.amount>0?"+":""}${x.amount} ${t("cur")}</b></div>`).join("");
  return `<h1 style="margin:10px 0">${t("history")}</h1><div class="seg"><a class="${S.htab=="orders"?"on":""}" onclick="S.htab='orders';render()">${t("orders")}</a><a class="${S.htab=="fin"?"on":""}" onclick="S.htab='fin';render()">${t("finance")}</a></div>${o||`<p style="color:var(--mut);text-align:center;margin-top:40px">—</p>`}`}
function friends(){const l=`https://t.me/${S.cat.bot}?start=${S.u.ref}`,c=(a,b)=>`<div class="card" style="text-align:center;margin:0"><h2>${a}</h2><small>${b}</small></div>`;
  return `<div class="hero"><small>+ ${t("bonus")}</small><h1>${t("invite")}</h1><p>${t("invsub")}</p></div>
  <div class="row3" style="margin-bottom:14px">${c(S.u.refs,t("invited"))}${c(S.u.buyers||0,t("buyers"))}${c(fmt(S.u.bonus),t("bonus"))}</div>
  <div class="card"><div class="lbl">${t("mylink")}</div><div class="card" style="background:var(--bg);color:var(--mut);word-break:break-all;padding:14px">${l}</div><div class="flex"><button class="btn" onclick="tg&&tg.openTelegramLink('https://t.me/share/url?url='+encodeURIComponent('${l}'))">${t("send")}</button><button class="btn" style="background:var(--card2)" onclick="navigator.clipboard.writeText('${l}')">${t("copy")}</button></div></div>
  <div class="card"><b>${t("rule")}</b> <span style="float:right;background:var(--ok);color:#fff;padding:4px 12px;border-radius:20px">2%</span></div>`}
function set(){const tgu=tg?.initDataUnsafe?.user||{};
  return `<h1 style="margin:10px 0 16px">${t("profile")}</h1><div class="card"><div class="top"><div class="av">${(tgu.first_name||"?")[0]}</div><div><b>${tgu.first_name||""}</b><br><small style="color:var(--mut)">ID: ${tgu.id||""}</small></div></div>
  <div class="row3" style="grid-template-columns:1fr 1fr"><div class="card" style="margin:0"><small>${t("balance")}</small><h2>${fmt(S.u.balance)}</h2></div><div class="card" style="margin:0"><small>${t("spent")}</small><h2 style="color:#f59a0b">${fmt(S.u.spent)}</h2></div></div><button class="btn" style="margin-top:14px" onclick="go('topup')">${t("topup")}</button></div>
  <div class="card"><div class="lbl">${t("lang")}</div><div class="seg" style="margin:0">${[["uz","O'zbek"],["tg","Тоҷикӣ"],["ru","Русский"],["en","English"]].map(([k,n])=>`<a class="${LANG==k?"on":""}" onclick="chLang('${k}')">${n}</a>`).join("")}</div></div>
  <div class="card li" onclick="document.body.classList.toggle('light');localStorage.setItem('light',document.body.classList.contains('light')?1:'');render()"><b>🌙 ${t("night")}</b><div class="sw ${document.body.classList.contains("light")?"off":""}"></div></div>
  <div class="card"><div class="li" onclick="tg&&tg.openTelegramLink('https://t.me/'+S.cat.support)"><b>💬 ${t("support")}</b>›</div><div class="li" onclick="go('friends')"><b>👥 ${t("invite")}</b>›</div></div>`}
async function chLang(l){await setLang(l);api("/api/lang",{lang:l});render()}
init();
