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
  const v=S.view,m={menu,game,topup,meth,hist,friends,set,pay:payv},sub=["game","topup","meth","pay"].includes(v);
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
  return `<div class="card" style="display:flex;justify-content:space-between;align-items:center;padding:14px 16px" onclick="pickM('${m.id}')"><div class="flex" style="align-items:center"><div class="av" style="background:${m.color};border-radius:14px">${m.icon}</div><div><b>${m.name}</b><br><small style="color:var(--mut)">${t(m.type=="card"?"bycard":"byphone")}</small></div></div><div style="text-align:right"><b style="color:#8b7bff">${amt}</b> ›</div></div>`}).join("");
  return `<a style="color:#8b7bff;font-weight:600" onclick="go('topup')">‹ ${t("changeamt")}</a><div class="lbl" style="margin-top:18px">${t("paymethod")}</div>${rows||`<p style="color:var(--mut)">—</p>`}`}
async function pickM(id){const r=await api("/api/topup",{amount:S.amt,method:id});if(r?.ok){S.pay=r;S.file=null;go("pay")}else alert(t("err"))}
function payv(){const p=S.pay||{};
  return `<a style="color:#8b7bff;font-weight:600" onclick="go('meth')">‹ ${t("changemeth")}</a>
  <div class="card" style="margin-top:14px;text-align:center"><div class="lbl">${t("payto")}</div><div class="av" style="background:${p.color};border-radius:18px;width:72px;height:72px;margin:6px auto 14px;font-size:26px">${p.icon}</div>
  <h1 onclick="cp(S.pay.pay)" style="font-size:40px">${p.pay} <span style="color:#8b7bff;font-size:20px">${p.cur=="RUB"?"₽":t("cur")}</span> 📋</h1><small style="color:var(--mut)">${t("tapcopy")}</small>
  <div class="card" style="margin:16px 0 0;text-align:left;background:var(--bg);display:flex;justify-content:space-between;align-items:center"><div><div class="lbl" style="margin:0 0 6px">${t(p.type=="card"?"cardno":"phoneno")}</div><b style="font-size:20px">${p.value}</b><br><small style="color:var(--mut)">${p.holder}</small></div><div class="av" style="background:var(--card2);border-radius:50%" onclick="cp(S.pay.value)">📋</div></div></div>
  <div style="text-align:center;color:var(--mut);margin:18px 0 10px">— ${t("afterpay")} —</div>
  <div class="card"><b>${t("uploadrc")}</b><label style="display:block;margin-top:14px;border:2px dashed var(--line);border-radius:18px;padding:26px;text-align:center;color:var(--mut)"><input type="file" accept="image/jpeg,image/png" style="display:none" onchange="pickF(this)">${S.file?`<b class="ok">✓ ${S.file.name}</b>`:`📷<br><b>${t("photo")}</b><br><small>JPG, PNG — 5MB</small>`}</label></div>
  <button class="btn" ${S.file?"":"disabled"} onclick="sendRc()">✅ ${t("sendconfirm")}</button>`}
function pickF(el){const f=el.files[0];if(!f)return;if(f.size>5*1024*1024)return alert("5MB");S.file=f;render()}
function toJpeg(f){return new Promise((ok,no)=>{const im=new Image();im.onload=()=>{const k=Math.min(1,1280/Math.max(im.width,im.height)),c=document.createElement("canvas");c.width=im.width*k;c.height=im.height*k;c.getContext("2d").drawImage(im,0,0,c.width,c.height);ok(c.toDataURL("image/jpeg",.8))};im.onerror=no;im.src=URL.createObjectURL(f)})}
async function sendRc(){const b=document.querySelector(".btn");b.disabled=true;
  try{const img=await toJpeg(S.file);const r=await api("/api/receipt",{id:S.pay.id,method:S.pay.method,image:img});
    if(r?.ok){alert(t("rcpt_ok"));S.file=null;S.amt=0;go("menu")}else{alert(t("err"));b.disabled=false}}catch(e){alert(t("err"));b.disabled=false}}
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
