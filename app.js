const API=""; // bir xil server
const T0=Date.now();
const tg=window.Telegram?.WebApp;tg?.ready();tg?.expand();
const $=s=>document.querySelector(s);
const S={u:{balance:0,spent:0,ref:"",refs:0,bonus:0},cat:{games:[],bot:"",support:""},tab:"games",view:"menu",game:null,sel:null,pid:"",region:"",hist:{orders:[],fin:[]},htab:"orders"};
async function api(p,b){try{const r=await fetch(API+p,{method:b?"POST":"GET",headers:{"Content-Type":"application/json","X-Init":tg?.initData||""},body:b?JSON.stringify(b):undefined});const j=await r.json();if(j&&j.error=="sub"&&!S.locked)lock(j.channels);return j}catch(e){return null}}
const SUBT={uz:["Obuna bo'ling","Ilovadan foydalanish uchun quyidagi kanallarga obuna bo'ling","✅ Tekshirish","Siz hali hamma kanalga obuna bo'lmagansiz!"],tg:["Обуна шавед","Барои истифодаи барнома ба каналҳои зерин обуна шавед","✅ Тафтиш","Шумо ҳанӯз ба ҳамаи каналҳо обуна нашудаед!"],ru:["Подпишитесь","Чтобы пользоваться приложением, подпишитесь на каналы ниже","✅ Проверить","Вы ещё не подписались на все каналы!"],en:["Subscribe","Please subscribe to the channels below to use the app","✅ Check","You haven't subscribed to all channels yet!"]};
function lock(chs){S.locked=true;const s=SUBT[LANG]||SUBT.ru;$("#splash").classList.add("hide");$("#nav").style.display="none";if(tg)tg.BackButton.hide();
  $("#app").innerHTML=`<div style="padding:40px 16px;text-align:center"><div style="font-size:56px">🔒</div><h2 style="margin:12px 0 6px">${s[0]}</h2><p style="color:var(--mut);margin:0 0 20px">${s[1]}</p>`+(chs||[]).map(c=>`<a class="btn" style="display:block;margin-bottom:10px;text-decoration:none;box-sizing:border-box" href="${esc(c.url)}" onclick="event.preventDefault();openCh('${esc(c.url)}')">📢 ${esc(c.name)}</a>`).join("")+`<button class="btn" style="margin-top:10px;background:#16a34a" onclick="unlock()">${s[2]}</button></div>`}
function openCh(u){if(tg&&u.includes("t.me"))tg.openTelegramLink(u);else window.open(u,"_blank")}
async function unlock(){const s=SUBT[LANG]||SUBT.ru;const r=await api("/api/me");if(r&&!r.error){S.locked=false;$("#nav").style.display="";init()}else if(r&&r.error=="sub"){lock(r.channels);(tg?.showAlert?tg.showAlert(s[3]):alert(s[3]))}}
const fmt=n=>(+n).toLocaleString("ru",{maximumFractionDigits:2});
const go=async v=>{S.view=v;if(v=="hist"){const r=await api("/api/history");if(r)S.hist=r}render();scrollTo(0,0)};
const NAV=[["menu","grid","menu"],["hist","hist","history"],["friends","users","friends"],["set","user","settings"]];
async function init(){
  const [,me,cat]=await Promise.all([setLang(localStorage.getItem("lang")||"ru"),api("/api/me"),api("/api/catalog")]);
  if(S.locked)return;
  if(me&&!me.error){S.u=me;if(me.lang&&me.lang!==LANG)await setLang(me.lang)}
  if(cat)S.cat=cat;
  if(localStorage.getItem("light"))document.body.classList.add("light");
  render();if(new URLSearchParams(location.search).get("go")=="hist")go("hist");setTimeout(()=>$("#splash").classList.add("hide"),Math.max(0,1500-(Date.now()-T0)))}
function render(){
  if(S.locked)return;
  const v=S.view,m={menu,game,topup,meth,hist,friends,set,rev,top:topv,res:resv,adm,admg,pay:payv},sub=["game","topup","meth","pay","rev","res","adm","admg"].includes(v);
  $("#app").innerHTML=m[v]();
  $("#nav").style.display=v=="res"?"none":"";
  $("#nav").innerHTML=NAV.map(([k,i,n])=>`<a class="${v==k||(k=="menu"&&sub)||(k=="friends"&&v=="top")||(k=="set"&&(v=="adm"||v=="admg"))?"on":""}" onclick="go('${k}')">${I(i)}<span>${t(n)}</span></a>`).join("");
  if(tg)tg.BackButton[(sub||v=="top")?"show":"hide"]()}
tg?.BackButton.onClick(()=>go(({top:"friends",admg:"adm",adm:"set"})[S.view]||"menu"));
const bdg=g=>g.dx?'<b class="bdg a">AUTO</b>':g.new?'<b class="bdg n">NEW</b>':"";
const iu=id=>String(id).startsWith("g_")?`/ico/${id}`:`/${id}.png?v=6`;
const gi=g=>`<img class="gimg" src="${iu(g.id)}" onerror="this.style.display='none'">`;
function menu(){const u=S.u,tgu=tg?.initDataUnsafe?.user||{};
  const games=S.cat.games.map(g=>`<div class="game" onclick="openGame('${g.id}')"><i style="background:${g.color}">${gi(g)}${g.icon}${bdg(g)}</i>${g.name}</div>`).join("");
  const gifts=(S.cat.gifts||[]).map(g=>`<div class="li"><div><b>${g.name}</b><br><small style="color:var(--mut)">${g.sub}</small></div>›</div>`).join("");
  const ai=(S.cat.ai||[]).map(g=>`<div class="pk"><b>${g.name}</b><span>${g.price} c.</span></div>`).join("");
  const body=S.tab=="games"?`<div class="grid3">${games}</div>`:S.tab=="gift"?`<div class="card">${gifts}</div>`:`<div class="grid3" style="grid-template-columns:1fr 1fr">${ai}</div>`;
  return `<div class="top"><div class="av">${tgu.photo_url?`<img src="${tgu.photo_url}">`:(tgu.first_name||"?")[0]}</div><div><b>${tgu.first_name||""}</b><br><small style="color:var(--mut)">${tgu.username?"@"+tgu.username:""}</small></div></div>
  <div class="bal"><small>${t("balance")}</small><h2>${fmt(u.balance)} <span>${t("cur")}</span></h2>
  <div class="row3"><div class="glass" onclick="go('topup')"><svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M19 7V5a2 2 0 0 0-2-2H5a2 2 0 0 0 0 4h14a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5"/><path d="M16 13.5h2"/></svg><span>${t("btn_topup")}</span></div><div class="glass" onclick="alert(t('nopromo'))"><svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2z"/><path d="M13 5v2"/><path d="M13 17v2"/><path d="M13 11v2"/></svg><span>${t("btn_bonus")}</span></div><div class="glass" onclick="tg&&tg.openTelegramLink('https://t.me/'+S.cat.support)"><svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg><span>${t("support")}</span></div></div></div>
  <div class="card" style="display:flex;align-items:center;gap:14px;padding:16px 18px" onclick="openReviews()"><div class="av" style="background:#3a3320;border-radius:14px;font-size:26px">⭐</div><div style="flex:1"><b style="font-size:24px">${(u.rating&&u.rating.count)?u.rating.avg.toFixed(1):"—"}</b> <span style="color:#facc15">★★★★★</span> <small style="color:var(--mut)">· ${(u.rating&&u.rating.count)||0} ${t("ratings_n")}</small></div><span style="color:var(--mut)">›</span></div>
  <div class="seg"><a class="${S.tab=="games"?"on":""}" onclick="S.tab='games';render()">${t("games")}</a><a class="${S.tab=="gift"?"on":""}" onclick="S.tab='gift';render()">Gift Code</a><a class="${S.tab=="ai"?"on":""}" onclick="S.tab='ai';render()">🤖 AI</a></div>${body}`}
const gfields=g=>(g.fields&&g.fields.length)?g.fields:[{key:"player_id",label:""}];
const flabel=f=>f.key=="player_id"?t("enterid"):f.key=="telegram_username"?"Telegram @username":(f.label||f.key);
const gregs=g=>g.regions||[];
const qtyOk=g=>!!g.stars&&S.qty>=g.stars.min&&S.qty<=g.stars.max;
const starsTotal=g=>Math.ceil(g.stars.unit*S.qty*10-1e-9)/10;
function openGame(id){const g=S.cat.games.find(x=>x.id==id);if(!g)return;S.game=g;S.sel=null;S.fv={};S.checked=false;S.nick="";S.idmsg="";S.nowarn=false;S.checking=false;
  S.qty=g.stars?(g.stars.presets[0]||g.stars.min):1;S.region=g.clan?"":(gregs(g)[0]||"");S.ack1=S.ack2=false;S.ptab=Object.keys(g.tabs)[0]||"";if(g.clan)S.sel=((Object.values(g.tabs)[0]||[])[0]||{}).id||null;go("game")}
const availTabs=g=>Object.keys(g.tabs).filter(k=>g.tabs[k].some(i=>!i.region||!S.region||i.region==S.region));
function pickR(i){S.region=gregs(S.game)[i];if(!S.game.clan)S.sel=null;render()}
function pickT(i){S.ptab=availTabs(S.game)[i];S.sel=null;render()}
function setQty(v,live){S.qty=Math.max(0,Math.floor(+v||0));if(!live)return render();const g=S.game,b=$("#bbtn"),tt=$("#tot");if(tt)tt.textContent=fmt(starsTotal(g))+" "+t("cur");if(b)b.disabled=!(S.checked&&qtyOk(g))}
function game(){const g=S.game;if(!g)return"";if(g.clan)return clanv(g);
  const fs=gfields(g),regs=gregs(g),tabs=availTabs(g);if(!tabs.includes(S.ptab))S.ptab=tabs[0]||S.ptab;const items=(g.tabs[S.ptab]||[]).filter(i=>!i.region||!S.region||i.region==S.region),vals=fs.map(f=>S.fv[f.key]||"").join(" / ");
  const idcard=S.checked?`<div style="display:flex;align-items:center;gap:14px;background:#10302a;border:1px solid #1a5c4a;border-radius:20px;padding:14px 16px"><div style="width:48px;height:48px;border-radius:50%;background:#16463b;color:#22c993;display:grid;place-items:center;flex:none">${I("check",24)}</div><div style="flex:1;min-width:0">${S.nick?`<b class="tr" style="font-size:18px">«${esc(S.nick)}»</b><div class="ok" style="font-size:15px">${esc(vals)}</div>`:S.nowarn?`<b class="tr" style="font-size:18px">${esc(vals)}</b>`:`<b class="tr" style="font-size:18px">ID: ${esc(vals)}</b><div style="color:#f5a623;font-size:14px;margin-top:4px">⚠ ${t("id_unv")}</div>`}</div><a onclick="S.checked=false;S.nick='';render()" style="color:var(--mut);flex:none">${t("change")}</a></div>`
   :`${fs.map(f=>`<input placeholder="${esc(flabel(f))}" value="${esc(S.fv[f.key]||"")}" oninput="S.fv['${f.key}']=this.value" style="margin-bottom:10px">`).join("")}<button class="btn" ${S.checking?"disabled":""} onclick="chk()">${S.checking?t("checking"):(g.nocheck?t("continue"):t("check"))}</button>${S.idmsg?`<div style="color:var(--bad);margin-top:10px;font-size:14px">${t(S.idmsg=="noid"?"id_bad":"id_fmt")}</div>`:""}`;
  const rc=regs.length?`<div class="card"><div class="lbl">${t("region")}</div><div class="reg">${regs.map((r,i)=>`<a class="${S.region==r?"on":""}" onclick="pickR(${i})">${esc((g.region_titles&&g.region_titles[r])||r)}</a>`).join("")}</div></div>`:"";
  const sc=g.stars?`<div class="card"><div class="lbl">${t("qty")}</div><div class="reg chips" style="margin:0 0 12px">${g.stars.presets.map(p=>`<a class="${S.qty==p?"on":""}" onclick="setQty(${p})">${p} ⭐</a>`).join("")}</div><input type="number" inputmode="numeric" min="${g.stars.min}" max="${g.stars.max}" value="${S.qty}" oninput="setQty(this.value,1)"><div style="display:flex;justify-content:space-between;margin-top:14px;font-size:18px"><b>${t("total")}</b><b id="tot">${fmt(starsTotal(g))} ${t("cur")}</b></div><small style="color:var(--mut)">${g.stars.min} – ${g.stars.max}</small></div>`:"";
  const tb=(!g.stars&&tabs.length>1)?`<div class="seg">${tabs.map((k,i)=>`<a class="${S.ptab==k?"on":""}" onclick="pickT(${i})">${esc(k)}</a>`).join("")}</div>`:"";
  const grid=g.stars?"":`<div class="lbl">${t("pick")}</div>${tb}<div class="grid3" style="grid-template-columns:1fr 1fr">${items.map(i=>`<div class="pk ${S.sel==i.id?"on":""}" onclick="S.sel='${esc(i.id)}';render()">${i.off?`<em>-${i.off}%</em>`:""}<b>${esc(i.name)}</b><span>${fmt(i.price)} ${t("cur")}</span></div>`).join("")}</div>`;
  const can=S.checked&&(g.stars?qtyOk(g):!!S.sel);
  return `<div class="card top" style="margin:0 0 14px"><div class="av" style="background:${g.color};border-radius:14px;position:relative">${gi(g)}${g.icon}</div><div><b>${g.name}</b><br><small style="color:var(--mut)">${g.sub}</small></div></div>
  ${(g.info||[]).map(b=>`<div class="card">${b.img?`<img src="${esc(b.img)}" style="width:100%;border-radius:14px;display:block">`:""}${b.txt?`<div style="${b.img?"margin-top:12px;":""}white-space:pre-wrap;line-height:1.5;font-size:15px">${esc(b.txt)}</div>`:""}</div>`).join("")}
  ${(!g.stars&&!Object.keys(g.tabs).length)?`<div class="card" style="color:var(--mut);text-align:center">${t("soon")}</div>`:`<div class="card"><div class="lbl">${g.nocheck?"TELEGRAM":t("playerid")}</div>${idcard}</div>${rc}${sc}${grid}
  <div class="buy"><button class="btn" id="bbtn" ${can?"":"disabled"} onclick="buy()">${t("choose")}</button></div>`}`}

const CL={
uz:{intro:"Botlar sizning klaningiz nomidan o'yinga kirib, shon ballarini yig'adi. Ballar, daraja va a'zolar buyurtma sahifasida jonli ko'rinadi.",s1:"Avval o'yinda klanni sozlang",s1s:"O'yinda: Klan → Klan sozlamalari → <b>Tasdiqlash usuli</b>. Aynan rasmdagidek qiling:",
 b:["<b>Avto tasdiqlash — «Yoqilgan».</b> Shunda botlar klanga sizning ruxsatingizsiz o'zlari kiradi.","<b>Daraja, KB-reyting, BO-reyting — «Standart».</b> Daraja yoki reytingga cheklov qo'ysangiz, botlar kira olmaydi.","Klanda <b>bo'sh o'rinlar</b> bo'lishi kerak.","Xizmat ishlayotgan vaqtda bu sozlamalarni o'zgartirmang."],
 a1:"Men klanni aynan shunday sozladim. Sozlamalar noto'g'ri bo'lib, ballar tushmasa, <b>javobgarlik o'zimda</b> — bunday ishga tushirish uchun pul qaytarilmaydi.",s2:"Klan va region",id:"Klan ID",ph:"Masalan, 3012345678",note:"Norasmiy xizmat. Faqat klan ID sini kiriting, o'yin akkauntining parolini hech qachon kiritmang.",hint:"O'yinda: Klan → klan haqida ma'lumot → ID.",reg:"Klan serveri regioni",
 w:"Ishga tushirishdan oldin o'qing:",wl:["Klaningiz joylashgan <b>regionni tanlang</b>. Region noto'g'ri bo'lsa, ballar tushmaydi.","Ishga tushirilgandan keyin pul <b>qaytarilmaydi</b>. Agar ishga tushmasa, buyurtma rad etiladi va pul balansingizga qaytariladi.","Ballni botlar bilan oshirishni o'yin qoidabuzarlik deb hisoblashi mumkin. Qaror va xavf — klan egasida."],a2:"Men o'qidim va roziman",go:"Ishga tushirish"},
tg:{intro:"Ботҳо аз номи кланатон ба бозӣ даромада, холҳои шуҳрат ҷамъ мекунанд. Холҳо, сатҳ ва аъзоёни клан дар саҳифаи фармоиш зинда намоён мешаванд.",s1:"Аввал клан-ро дар бозӣ танзим кунед",s1s:"Дар бозӣ: Клан → Танзимоти клан → <b>Усули тасдиқ</b>. Айнан мисли расм кунед:",
 b:["<b>Тасдиқи худкор — «Фаъол».</b> Он гоҳ ботҳо бе иҷозати шумо худашон ба клан медароянд.","<b>Сатҳ, КБ-рейтинг, БО-рейтинг — «Пешфарз».</b> Агар маҳдудият гузоред, ботҳо дароида наметавонанд.","Дар клан бояд <b>ҷойҳои холӣ</b> бошанд.","То кори хизмат ин танзимотро тағйир надиҳед."],
 a1:"Ман клан-ро айнан ҳамин тавр танзим кардам. Агар танзимот нодуруст бошад ва холҳо наояд, <b>масъулият бар дӯши худам</b> — барои чунин оғоз пул баргардонида намешавад.",s2:"Клан ва минтақа",id:"ID-и клан",ph:"Масалан, 3012345678",note:"Хизмати ғайрирасмӣ. Танҳо ID-и клан-ро ворид кунед, рамзи ҳисоби бозиро ҳеҷ гоҳ ворид накунед.",hint:"Дар бозӣ: Клан → маълумот дар бораи клан → ID.",reg:"Минтақаи сервери клан",
 w:"Пеш аз оғоз хонед:",wl:["<b>Минтақаеро интихоб кунед</b>, ки клани шумо дар он аст. Минтақаи нодуруст — холҳо намеояд.","Пас аз оғоз пул <b>баргардонида намешавад</b>. Агар оғоз нашавад, фармоиш рад шуда, пул ба баланс бармегардад.","Бозӣ метавонад баландбардории холро бо ботҳо вайронкунии қоидаҳо ҳисоб кунад. Қарор ва хатар — бар дӯши соҳиби клан."],a2:"Ман хондам ва розӣ ҳастам",go:"Оғоз кардан"},
ru:{intro:"Боты заходят в игру за ваш клан и набирают очки славы. Очки, уровень и участников клана видно вживую на странице заказа.",s1:"Сначала настройте клан в игре",s1s:"В игре: Клан → Настройки клана → <b>Метод подтверждения</b>. Сделайте точно как на картинке:",
 b:["<b>Авто подтверждение — «Вкл.»</b> Тогда боты вступают в клан сами, без вашего одобрения.","<b>Ур., КБ-рейтинг, БО-рейтинг — «По умолчанию».</b> Если поставить ограничение по уровню или рейтингу, боты не смогут вступить.","В клане должны быть <b>свободные места</b>.","Не меняйте эти настройки, пока сервис работает."],
 a1:"Я настроил клан точно так. Если настройки неверные и очки не пошли, <b>отвечаю я сам</b> — деньги за такой запуск не возвращаются.",s2:"Клан и регион",id:"ID клана",ph:"Например, 3012345678",note:"Неофициальный сервис. Вводите только ID клана, никогда не вводите пароль от игрового аккаунта.",hint:"В игре: Клан → информация о клане → ID.",reg:"Регион сервера клана",
 w:"Перед запуском прочитайте:",wl:["Выберите <b>тот регион, где ваш клан</b>. Не тот регион — очки не пойдут.","После запуска деньги <b>не возвращаются</b>. Не запустилось — заказ отклонят и деньги вернутся на ваш баланс.","Накрутку очков ботами игра может посчитать нарушением правил. Решение и риск — на владельце клана."],a2:"Я прочитал и согласен",go:"Запустить"},
en:{intro:"Bots join the game for your clan and earn glory points. Points, level and clan members are visible live on the order page.",s1:"First, set up your clan in the game",s1s:"In game: Clan → Clan settings → <b>Approval method</b>. Do exactly as in the picture:",
 b:["<b>Auto approval — “On”.</b> Then bots join the clan by themselves, without your approval.","<b>Level, KB rating, BO rating — “Default”.</b> If you set a level or rating limit, bots can't join.","The clan must have <b>free slots</b>.","Don't change these settings while the service is running."],
 a1:"I set up the clan exactly like this. If the settings are wrong and no points are earned, <b>I am responsible</b> — money for such a launch is not refunded.",s2:"Clan and region",id:"Clan ID",ph:"E.g. 3012345678",note:"Unofficial service. Enter only the clan ID, never enter your game account password.",hint:"In game: Clan → clan info → ID.",reg:"Clan server region",
 w:"Read before launching:",wl:["Choose <b>the region where your clan is</b>. Wrong region — no points.","After launch the money is <b>not refunded</b>. If it fails to start, the order is declined and the money returns to your balance.","The game may treat bot point farming as a rule violation. The decision and risk are the clan owner's."],a2:"I have read and agree",go:"Launch"}};
function clanv(g){const L=CL[LANG]||CL.ru,it=(Object.values(g.tabs)[0]||[])[0]||{price:0},cid=(S.fv.player_id||"").trim(),ok=S.ack1&&S.ack2&&S.region&&/^\d{5,14}$/.test(cid);
  const chk=(on,fn,txt)=>`<div onclick="${fn}" style="display:flex;gap:12px;align-items:flex-start;border:1px solid var(--line);border-radius:16px;padding:14px;margin-top:12px"><span style="flex:none;width:22px;height:22px;border-radius:6px;border:2px solid ${on?"#8b7bff":"var(--mut)"};background:${on?"#8b7bff":"none"};color:#fff;display:grid;place-items:center;font-size:15px;line-height:1">${on?"✓":""}</span><span style="line-height:1.45">${txt}</span></div>`;
  const info=(g.info||[]).map(b=>`${b.img?`<img src="${esc(b.img)}" style="width:100%;border-radius:14px;display:block;margin:12px 0">`:""}${b.txt?`<div style="white-space:pre-wrap;line-height:1.5;font-size:15px;margin:8px 0">${esc(b.txt)}</div>`:""}`).join("");
  const regs=gregs(g).map((r,i)=>`<div onclick="pickR(${i})" style="display:flex;align-items:center;gap:12px;border:1px solid ${S.region==r?"#8b7bff":"var(--line)"};background:${S.region==r?"#8b7bff1f":"none"};border-radius:16px;padding:14px;margin-bottom:8px"><span style="flex:none;width:20px;height:20px;border-radius:50%;border:2px solid ${S.region==r?"#8b7bff":"var(--mut)"};box-shadow:${S.region==r?"inset 0 0 0 4px var(--card)":"none"};background:${S.region==r?"#8b7bff":"none"}"></span><b style="flex:1">${esc((g.region_titles&&g.region_titles[r])||r)}</b><b>${fmt(it.price)} ${t("cur")}</b></div>`).join("");
  return `<div class="card top" style="margin:0 0 14px"><div class="av" style="background:${g.color};border-radius:14px;position:relative">${gi(g)}${g.icon}</div><div><b>${g.name}</b><br><small style="color:var(--mut)">${g.sub}</small></div></div>
  <p style="color:var(--mut);line-height:1.5;margin:0 4px 14px">${L.intro}</p>
  <div class="card"><div class="flex" style="align-items:center;gap:10px"><span style="width:32px;height:32px;border-radius:50%;background:#8b7bff;display:grid;place-items:center;font-weight:800;flex:none">1</span><b style="font-size:18px">${L.s1}</b></div><p style="color:var(--mut);margin:12px 0 0;line-height:1.5">${L.s1s}</p>${info}<ul style="padding-left:20px;line-height:1.5;margin:10px 0">${L.b.map(x=>`<li style="margin-bottom:8px">${x}</li>`).join("")}</ul>${chk(S.ack1,"S.ack1=!S.ack1;render()",L.a1)}</div>
  <div class="card"><div class="flex" style="align-items:center;gap:10px"><span style="width:32px;height:32px;border-radius:50%;background:#8b7bff;display:grid;place-items:center;font-weight:800;flex:none">2</span><b style="font-size:18px">${L.s2}</b></div>
   <div class="lbl" style="margin-top:14px">${L.id}</div><input inputmode="numeric" placeholder="${L.ph}" value="${esc(S.fv.player_id||"")}" oninput="S.fv.player_id=this.value;clanUpd()">
   <div style="background:#3a2f12;color:#facc15;border-radius:14px;padding:12px 14px;margin:12px 0;line-height:1.45">🛡 ${L.note}</div><small style="color:var(--mut)">${L.hint}</small>
   <div class="lbl" style="margin-top:16px">${L.reg}</div>${regs}
   <div style="background:#2a1414;border:1px solid #6b2a2a;border-radius:16px;padding:14px;margin-top:12px;color:#ff8a8a"><b>⚠ ${L.w}</b><ul style="padding-left:20px;line-height:1.5;margin:8px 0 0">${L.wl.map(x=>`<li style="margin-bottom:6px">${x}</li>`).join("")}</ul></div>
   ${chk(S.ack2,"S.ack2=!S.ack2;render()",L.a2)}</div>
  <div class="buy"><button class="btn" id="bbtn" ${ok?"":"disabled"} onclick="buy()">${L.go}${S.region?" · "+fmt(it.price)+" "+t("cur"):""}</button></div>`}
function clanUpd(){const b=$("#bbtn");if(b)b.disabled=!(S.ack1&&S.ack2&&S.region&&/^\d{5,14}$/.test((S.fv.player_id||"").trim()))}
async function chk(){const g=S.game,fs=gfields(g);S.idmsg="";
  for(const f of fs){const v=(S.fv[f.key]||"").trim();S.fv[f.key]=v;const ok=f.key=="telegram_username"?/^@?[A-Za-z0-9_]{5,32}$/.test(v):/^[#@\w.\-]{1,40}$/.test(v);if(!ok){S.idmsg="fmt";return render()}}
  S.pid=S.fv[fs[0].key];
  if(g.nocheck){S.nick="";S.nowarn=true;S.checked=true;return render()}
  S.nowarn=false;S.checking=true;render();
  const r=await api(`/api/checkid?game=${g.id}&region=${encodeURIComponent(S.region)}&fields=${encodeURIComponent(JSON.stringify(S.fv))}`);S.checking=false;
  if(r&&r.error=="noid"){S.idmsg="noid";return render()}
  if(r&&r.error=="bad"){S.idmsg="fmt";return render()}
  S.nick=(r&&r.nick)||"";S.checked=true;render()}
const CLK='<svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#14c38e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>';
function showRes(o){S.res=o;go("res")}
function resv(){const o=S.res||{};
  return `<div class="flex" style="align-items:center;gap:14px;margin:6px 0 4px"><div class="av" style="background:var(--card);border:1px solid var(--line);color:var(--tx);width:48px;height:48px" onclick="go('menu')">${I("back",22)}</div><h1 style="font-size:25px">${o.head||""}</h1></div>
  <div style="text-align:center;padding:34px 4px 14px"><div class="rg"><div class="rc">${CLK}</div></div><h1 style="font-size:30px;line-height:1.2;margin:28px 0 12px">${o.title||""}</h1><p style="color:var(--mut);font-size:17px;line-height:1.55">${o.body||""}</p></div>
  ${o.rows?`<div class="card" style="text-align:center;padding:20px">${o.rows}</div>`:""}
  <button class="btn" style="background:var(--card);border:1px solid var(--line);color:var(--tx);margin-top:8px;padding:18px" onclick="go('menu')">${t("tomenu")}</button>`}
function fundsModal(need,bal){const o=document.createElement("div");o.style.cssText="position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:30;display:flex;align-items:center;justify-content:center;padding:24px";
  o.innerHTML=`<div style="background:#101022;border:1px solid var(--line);border-radius:26px;padding:26px 22px;width:100%;max-width:340px;text-align:center"><div style="width:68px;height:68px;border-radius:50%;background:#3a1620;color:#ef4444;display:grid;place-items:center;margin:0 auto 14px">${I("wallet",32)}</div><h2 style="font-size:22px;margin-bottom:12px">${t("nofunds_t")}</h2><div style="color:var(--mut)">${t("balance")}: <b style="color:var(--tx)">${fmt(bal)} ${t("cur")}</b></div><div style="color:var(--mut);margin-top:4px">${t("need_l")}: <b style="color:var(--tx)">${fmt(need)} ${t("cur")}</b></div><div class="flex" style="margin-top:20px"><button class="btn" style="background:var(--card2)" id="fc">${t("close")}</button><button class="btn" id="ft">${t("topup")}</button></div></div>`;
  o.querySelector("#fc").onclick=()=>o.remove();o.querySelector("#ft").onclick=()=>{o.remove();go("topup")};document.body.appendChild(o)}
const pendModal=()=>modal(t("pend_title"),t("pend_body"),t("gotit"),()=>go("hist"),'<span style="font-size:68px;line-height:1">⏳</span>',"#f59e0b24");
async function buy(){const g=S.game,bt=document.querySelector(".buy .btn");if(bt)bt.disabled=true;
  const r=await api("/api/order",{game:g.id,item:g.stars?g.stars.id:S.sel,fields:S.fv,region:S.region,qty:S.qty,pid:Object.values(S.fv)[0],ack:!!(S.ack1&&S.ack2)});
  if(r?.error=="pending"){if(bt)bt.disabled=false;return pendModal()}
  if(r?.error=="noid"){S.checked=false;S.nick="";S.idmsg="noid";return render()}
  if(r?.error=="funds"){if(bt)bt.disabled=false;return fundsModal(r.need,r.balance)}
  if(r?.ok){S.u.balance=r.balance;const rows=`<div class="lbl" style="text-align:center">${t("product_l")}</div><b style="font-size:19px">${esc(r.game)} · ${esc(r.item)}</b><div style="color:var(--mut);margin-top:6px">${r.nick?"«"+esc(r.nick)+"» · ":""}${esc(Object.values(S.fv).join(" / "))}</div><div style="color:#8b7bff;font-weight:700;margin-top:6px">${fmt(r.price)} ${t("cur")}</div>`;showRes({head:t("res_wait")+" ⏳",title:t("ord_title"),body:t("ord_body"),rows})}else{if(bt)bt.disabled=false;alert(t("err")+(r&&r.error?" ("+r.error+")":" (net)"))}}
const CPY='<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#8b7bff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-left:6px"><rect x="9" y="9" width="12" height="12" rx="2.5"/><path d="M5 15V6a2 2 0 0 1 2-2h9"/></svg>';
const pi=id=>`<img class="gimg" src="${iu(id)}" onerror="this.style.display='none'">`;
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
async function pickM(id){const r=await api("/api/topup",{amount:S.amt,method:id});if(r?.ok){S.pay=r;S.file=null;go("pay")}else if(r?.error=="pending")pendModal();else alert(t("err"))}
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
    if(r?.ok){const p=S.pay||{};S.file=null;S.amt=0;showRes({head:t("res_wait")+" ⏳",title:t("rcpt_title"),body:t("rcpt_sent").replace("{a}","<b>"+p.amount+" "+t("cur")+"</b>"),rows:`<div class="lbl" style="text-align:center">${t("paymethod_l")}</div><b style="font-size:20px">${esc(p.name||"")}</b><div style="color:#8b7bff;font-weight:700;margin-top:6px">${p.amount} ${t("cur")}</div>`})}else if(r?.error=="pending"){pendModal();b.disabled=false}else if(r?.error=="dup"){alert(t("dup_rcpt"));b.disabled=false}else{alert(t("err"));b.disabled=false}}catch(e){alert(t("err"));b.disabled=false}}
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
  const c2=games.map(g=>chip(f.g==g,`setRf('g','${f.g==g?"":g}')`,`${gic(g)}${esc(g.replace(/\s/g,""))} ${R.items.filter(x=>x.game==g).length}`)).join("");
  const cards=it.map(x=>`<div class="card"><div class="flex" style="align-items:center"><div class="av" style="position:relative;background:hsl(${x.id*47%360} 55% 42%)">${esc((x.name||"?")[0].toUpperCase())}${avi(x.av)}</div><div style="flex:1"><b>${esc(x.name)}</b><br><span style="color:#facc15;font-size:15px">${"★".repeat(x.stars)}<span style="color:var(--line)">${"★".repeat(5-x.stars)}</span></span> <small style="background:var(--card2);color:var(--mut);padding:2px 8px;border-radius:8px;font-weight:700">${gic(x.game)}${esc(x.game.replace(/\s/g,""))}</small></div><small style="color:var(--mut)">${x.date}</small></div><div style="color:var(--mut);margin-top:10px">🛒 ${esc(x.item)}</div>${x.text?`<p style="margin-top:8px;line-height:1.4">${esc(x.text)}</p>`:""}${x.reply?`<div style="margin-top:10px;border-left:3px solid var(--pr);background:var(--bg);border-radius:10px;padding:10px 12px"><small style="color:#8b7bff;font-weight:700">🛡 Diavex Shop</small><br>${esc(x.reply)}</div>`:""}</div>`).join("");
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
check:'<path d="M5 12.5l4.5 4.5L19 7.5"/>',
chev:'<path d="M9 6l6 6-6 6"/>',
up:'<path d="M12 19V5M5.5 11.5L12 5l6.5 6.5"/>',
down:'<path d="M12 5v14M5.5 12.5L12 19l6.5-6.5"/>',
refresh:'<path d="M20 11A8 8 0 0 0 5.6 6.8L4 8.5"/><path d="M4 4v4.5h4.5"/><path d="M4 13a8 8 0 0 0 14.4 4.2l1.6-1.7"/><path d="M20 20v-4.5h-4.5"/>',
tup:'<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
tdn:'<path d="M3 7l6 6 4-4 8 8"/><path d="M15 17h6v-6"/>',
copy:'<rect x="9" y="9" width="12" height="12" rx="2.5"/><path d="M5 15V6a2 2 0 0 1 2-2h9"/>',
back:'<path d="M15 6l-6 6 6 6"/>',
tools:'<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.6 2.6-2.4-.6-.6-2.4z"/>',
trophy:'<path d="M8 4h8v5a4 4 0 0 1-8 0z"/><path d="M8 6H5.5a1 1 0 0 0-1 1c0 2 1.5 3.5 3.5 4M16 6h2.5a1 1 0 0 1 1 1c0 2-1.500 3.5-3.5 4M12 13v4M8.5 20h7M10 17h4"/>',
wallet:'<path d="M4 7.5A2.5 2.5 0 0 1 6.5 5H18v3"/><rect x="3.5" y="8" width="17" height="11.5" rx="2.5"/><path d="M16 13.8h2.2"/>'
};
const I=(k,w=24)=>`<svg width="${w}" height="${w}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${P[k]}</svg>`;
const ini=s=>esc([...String(s||"?")][0]||"?");
const gic=n=>{const id=gid(n);return id?`<img src="${iu(id)}" style="width:16px;height:16px;border-radius:5px;vertical-align:-3px;margin-right:4px;object-fit:cover" onerror="this.remove()">`:"🎮 "};
const avi=(u,i)=>u?`<img class="gimg" src="${u}" onerror="this.remove()">`:"";
const gid=n=>{const g=(S.cat.games||[]).find(x=>x.name==n);return g?g.id:""};
const ST={done:"st_done",pending:"st_wait",processing:"st_wait",cancelled:"st_cancel"};
function setH(k,v){S[k]=v;render()}
async function refreshHist(){const r=await api("/api/history");if(r){S.hist=r;render()}}
const admBack=(to,title)=>`<div class="flex" style="align-items:center;gap:14px;margin:6px 0 16px"><div class="av" style="background:var(--card);border:1px solid var(--line);color:var(--tx);width:48px;height:48px" onclick="go('${to}')">${I("back",22)}</div><h1 style="font-size:24px">${title}</h1></div>`;
async function admOpen(stay){const r=await api("/api/admin/games");if(!(r&&r.ok))return alert(t("err"));S.adm=r;
  if(!stay)return go("adm");if(S.view=="adm"){const y=scrollY;render();scrollTo(0,y)}}   // stay: foydalanuvchi boshqa sahifaga o'tib ketgan bo'lsa, uni qaytarib olib kirmaymiz
function adm(){const A=S.adm||{games:[],settings:{}};
  const row=(g,i)=>`<div class="card gr" style="${g.hidden?"opacity:.55":""}" onclick="admGame(${i})"><div class="av" style="width:64px;height:64px;background:${esc(g.color)};border-radius:16px;position:relative;flex:none">${esc(g.icon)}${pi(g.id)}</div><div style="flex:1;min-width:0"><b style="font-size:18px">${esc(g.name)}</b><br><small style="color:var(--mut);font-size:14px">${g.count} ta mahsulot${g.hidden?" · yashirin":""}</small></div><span style="color:var(--mut);font-size:24px">›</span></div>`;
  const all=A.games.map((g,i)=>[g,i]),vis=all.filter(x=>!x[0].hidden),hid=all.filter(x=>x[0].hidden);
  return `<div class="adm-wrap">`+admBack("set","🛠 Admin panel")+`<div class="card"><div class="lbl" style="margin-top:0">UMUMIY SOZLAMALAR</div><div class="flex"><div style="flex:1"><small style="color:var(--mut)">Ustama, %</small><input id="a_mk" type="number" step="0.5" value="${A.settings.markup}"></div><div style="flex:1"><small style="color:var(--mut)">1 USD = ? somoni</small><input id="a_rt" type="number" step="0.01" value="${A.settings.usd_tjs}"></div></div><small style="color:var(--mut);display:block;margin:10px 0">Donatix narxlariga qo'llanadi. Qo'lda o'zgartirilgan narxlarga ta'sir qilmaydi.</small><button class="btn" onclick="admSaveSet()">Saqlash</button></div>
  <div class="lbl">O'YINLAR (${vis.length})</div>${vis.map(x=>row(...x)).join("")}${hid.length?`<div class="lbl">YASHIRIN O'YINLAR (${hid.length})</div>`+hid.map(x=>row(...x)).join(""):""}</div>`}
async function admSaveSet(){const r=await api("/api/admin/save",{game:"",settings:{markup:+$("#a_mk").value,usd_tjs:+$("#a_rt").value}});if(r&&r.ok){toast("Saqlandi");S.cat=(await api("/api/catalog"))||S.cat;admOpen(true)}else alert((r&&r.msg)||t("err"))}
async function admLoad(id,keep,stay){const r=await api("/api/admin/game?id="+encodeURIComponent(id));if(!(r&&r.ok&&r.game))return alert(t("err"));
  S.ad={...r.game,ed:{},adds:[],dels:[],rg:{},newRegs:[],newTabs:[],trn:{},info:(r.game.info||[]).map(x=>({img:x.img||"",txt:x.txt||""})),cur:keep===undefined?null:keep,hide:r.game.hidden};if(!stay)return go("admg");if(S.view=="admg"){const y=scrollY;render();scrollTo(0,y)}}
function admGame(i){admLoad(S.adm.games[i].id)}
const admRegs=()=>{const a=S.ad,m=new Map();a.regions.forEach(x=>m.set(x.region,{...x}));a.newRegs.forEach(x=>m.set(x.region,{...x,fresh:1}));Object.entries(a.rg).forEach(([k,v])=>{if(m.has(k))Object.assign(m.get(k),v)});return [...m.values()]};
const admRows=()=>{const a=S.ad;const base=a.items.filter(x=>!a.dels.includes(x.id)).map(x=>({...x,...(a.ed[x.id]||{})}));const add=a.adds.map((x,i)=>({...x,id:"new"+i,src:"new",auto:null,ov:false}));return [...base,...add].filter(x=>a.cur===null||x.region==a.cur)};
function admE(id,k,v){const a=S.ad;if(id.startsWith("new")){const x=a.adds[+id.slice(3)];if(x)x[k]=k=="price"?+v:v;return}const e=(a.ed[id]=a.ed[id]||{});e[k]=k=="price"?+v:v;if(k=="price")delete e.reset}
function admT(id){const x=admRows().find(r=>r.id==id);if(!x)return;if(id.startsWith("new"))S.ad.adds[+id.slice(3)].hidden=!x.hidden;else(S.ad.ed[id]=S.ad.ed[id]||{}).hidden=!x.hidden;render()}
function admReset(id){const e=(S.ad.ed[id]=S.ad.ed[id]||{});e.reset=true;e.price=S.ad.items.find(r=>r.id==id).auto;render()}
function admD(id){if(id.startsWith("new"))S.ad.adds.splice(+id.slice(3),1);else if(!S.ad.dels.includes(id))S.ad.dels.push(id);render()}
function admCur(i){const rs=admRegs();S.ad.cur=i<0?null:rs[i].region;render()}
function admRegAdd(){const v=$("#a_nr").value.trim().slice(0,20);if(!/^[\w .\-]{1,20}$/.test(v))return alert("Region nomi: harf yoki raqam, 20 belgigacha");if(admRegs().some(r=>r.region==v)){S.ad.cur=v;return render()}S.ad.newRegs.push({region:v,title:"",hidden:false});S.ad.cur=v;render()}
function admRegE(k,v){const a=S.ad,nr=a.newRegs.find(x=>x.region==a.cur);if(nr){nr[k]=v;return}(a.rg[a.cur]=a.rg[a.cur]||{})[k]=v}
function admRegHide(){const r=admRegs().find(x=>x.region==S.ad.cur);if(!r)return;admRegE("hidden",!r.hidden);render()}
function admAdd(){const n=$("#a_n").value.trim().slice(0,60),p=+$("#a_p").value;if(!n||!(p>=0.1))return alert("Nom va narxni kiriting (narx kamida 0.1)");
  S.ad.adds.push({name:n,price:p,region:S.ad.cur||"",tab:($("#a_t").value.trim().slice(0,20))||"📦",sku:$("#a_s").value.trim().slice(0,60),hidden:false});render()}
const admTabs=()=>{const a=S.ad,s=new Set(a.tabs||[]);(a.newTabs||[]).forEach(x=>s.add(x));return [...s]};
function admTabAdd(){const v=$("#a_nt").value.trim().slice(0,24);if(!v)return;if(!admTabs().includes(v))S.ad.newTabs.push(v);render()}
function admTR(i,v){const a=S.ad,o=admTabs()[i];if(o===undefined)return;const nt=a.newTabs.indexOf(o);if(nt>=0)a.newTabs[nt]=v.slice(0,24);else a.trn[o]=v.slice(0,24)}
const admRenPending=()=>Object.entries(S.ad.trn||{}).map(([from,to])=>({from,to:String(to).trim()})).filter(x=>x.to&&x.to!=x.from);
const admDirty=()=>{const a=S.ad;return a&&(admRenPending().length||Object.keys(a.ed).length||a.adds.length||a.dels.length||Object.keys(a.rg).length||a.newRegs.length||a.hide!==a.hidden)};
function admg(){const a=S.ad;if(!a)return"";const rs=admRegs(),cr=rs.find(x=>x.region==a.cur),rows=admRows(),tabs=admTabs();
  const chips=`<div class="card"><div class="lbl" style="margin-top:0">REGION TANLANG</div><div class="rchips"><a class="${a.cur===null?"on":""}" onclick="admCur(-1)">Hammasi</a>${rs.map((r,i)=>`<a class="${a.cur===r.region?"on":""}${r.hidden?" off":""}" onclick="admCur(${i})">${esc(r.title||r.region)}</a>`).join("")}</div></div>`;
  const regCard=cr?`<div class="card"><div class="lbl" style="margin-top:0">REGION: ${esc(cr.region)}</div><input placeholder="Ko'rinadigan nom (ixtiyoriy)" value="${esc(cr.title||"")}" oninput="admRegE('title',this.value)" style="margin-bottom:12px"><div class="flex" style="align-items:center;justify-content:space-between"><b>${cr.hidden?"Yashirin (mijoz ko'rmaydi)":"Ko'rinadi"}</b><div class="sw ${cr.hidden?"off":""}" onclick="admRegHide()"></div></div></div>`:"";
  const list=rows.map(x=>{const id=esc(x.id),del=(x.src=="cust"||x.src=="new"),src={dx:"Donatix",static:"oddiy",cust:"qo'lda",new:"yangi (saqlanmagan)",stars:"Donatix"}[x.src]||"";
    const ov=x.auto!=null&&(x.ov||(a.ed[x.id]&&a.ed[x.id].price!==undefined&&a.ed[x.id].price!=x.auto));
    return `<div class="card pc" style="${x.hidden?"opacity:.5":""}"><div class="flex" style="align-items:center;gap:12px;margin-bottom:12px"><input value="${esc(x.name)}" oninput="admE('${id}','name',this.value)" ${x.src=="stars"?"disabled":""} style="flex:1;font-weight:700"><div class="sw ${x.hidden?"off":""}" onclick="admT('${id}')" title="Ko'rsatish / yashirish"></div></div>
    <div class="flex" style="gap:12px"><div style="flex:1"><small class="fl">Narx (somoni)</small><input type="number" step="0.01" value="${x.price}" oninput="admE('${id}','price',this.value)"></div>${x.src=="stars"?"":`<div style="flex:1"><small class="fl">Guruh</small><select onchange="admE('${id}','tab',this.value)">${(tabs.includes(x.tab)?tabs:[...tabs,x.tab]).map(tn=>`<option value="${esc(tn)}" ${tn==x.tab?"selected":""}>${esc(a.trn&&a.trn[tn]||tn)}</option>`).join("")}</select></div>`}</div>
    <div class="meta"><span class="pill">${esc(x.region||"hamma region")}</span><span class="pill">${src}</span>${x.auto!=null?`<span class="pill">avto narx: ${x.auto}</span>`:""}${ov?`<a class="pill lk" onclick="admReset('${id}')">↺ avtoga qaytarish</a>`:""}${x.sku?`<span class="pill">kod: ${esc(x.sku)}</span>`:""}${del?`<a class="pill dl" onclick="admD('${id}')">🗑 o'chirish</a>`:""}</div></div>`}).join("");
  const cnt=tn=>a.items.filter(x=>x.tab==tn&&!a.dels.includes(x.id)).length;
  const groups=a.stars?"":`<div class="card"><div class="lbl" style="margin-top:0">GURUHLAR</div>${tabs.map((tn,i)=>{const nw=a.newTabs.includes(tn),v=nw?tn:(a.trn[tn]!==undefined?a.trn[tn]:tn);return `<div class="flex" style="gap:10px;align-items:center;margin-bottom:10px"><input value="${esc(v)}" oninput="admTR(${i},this.value)" style="flex:1"><span class="pill">${nw?"yangi":cnt(tn)+" ta"}</span></div>`}).join("")}<div class="flex" style="gap:10px;margin-top:4px"><input id="a_nt" placeholder="Yangi guruh nomi" style="flex:1"><button class="btn" style="width:auto;padding:0 22px" onclick="admTabAdd()">＋</button></div><small style="color:var(--mut);display:block;margin-top:10px">Guruh nomini o'zgartiring va pastdagi <b>Saqlash</b> ni bosing. Mahsulotni boshqa guruhga o'tkazish: mahsulot kartasidagi «Guruh» ro'yxatidan tanlang.</small></div>`;
  return `<div class="adm-wrap"><div class="flex" style="align-items:center;gap:14px;margin:6px 0 16px"><div class="av" style="background:var(--card);border:1px solid var(--line);color:var(--tx);width:48px;height:48px;flex:none" onclick="go('adm')">${I("back",22)}</div><h1 style="font-size:24px;flex:1">${esc(a.name)}</h1></div>
  <div class="card flex" style="align-items:center;justify-content:space-between"><div><b>${a.hide?"Mijozlarga ko'rinmaydi":"Mijozlarga ko'rinadi"}</b><br><small style="color:var(--mut)">O'yinni yashirish / ko'rsatish</small></div><div class="sw ${a.hide?"off":""}" onclick="S.ad.hide=!S.ad.hide;render()"></div></div>
  ${chips}${regCard}
  <div class="lbl">MAHSULOTLAR (${rows.length})</div>${list||`<p style="color:var(--mut)">Bu yerda mahsulot yo'q.</p>`}
  <div class="card"><div class="lbl" style="margin-top:0">YANGI MAHSULOT ${a.cur?"("+esc(a.cur)+")":""}</div><input id="a_n" placeholder="Nomi (masalan: 100 Diamonds)" style="margin-bottom:12px"><div class="flex" style="margin-bottom:12px;gap:12px"><input id="a_p" type="number" step="0.01" placeholder="Narx (somoni)" style="flex:1"><input id="a_t" list="a_tl" placeholder="Guruh (💎)" style="flex:1"><datalist id="a_tl">${tabs.map(tn=>`<option value="${esc(tn)}">`).join("")}</datalist></div><input id="a_s" placeholder="Donatix mahsulot kodi (ixtiyoriy)" style="margin-bottom:12px"><button class="btn" style="background:var(--card2)" onclick="admAdd()">＋ Mahsulot qo'shish</button></div>
  ${groups}
  ${a.infoblocks?`<div class="card"><div class="lbl" style="margin-top:0">RASM VA TAVSIF</div>${(a.info||[]).map((b,i)=>`<div style="margin-bottom:14px;padding-bottom:14px;border-bottom:1px solid var(--line)">${b.img?`<img src="${esc(b.img)}" style="width:100%;border-radius:14px;display:block;margin-bottom:10px">`:""}<div class="flex" style="gap:8px;margin-bottom:8px"><label class="btn" style="width:auto;flex:1;padding:13px;background:var(--card2);text-align:center;margin:0">🖼 ${b.img?"Rasmni almashtirish":"Rasm tanlash"}<input type="file" accept="image/*" style="display:none" onchange="admInfoPick(${i},this)"></label>${b.img?`<button class="btn" style="width:auto;padding:0 14px;background:var(--card2)" onclick="admInfoRm(${i},1)">✕</button>`:""}<button class="btn" style="width:auto;padding:0 14px;background:var(--card2);color:#f87171" onclick="admInfoRm(${i})">🗑</button></div><textarea rows="5" placeholder="Tavsif (rasm tagida ko'rinadi)" oninput="S.ad.info[${i}].txt=this.value">${esc(b.txt||"")}</textarea></div>`).join("")}<div class="flex" style="gap:8px"><button class="btn" style="background:var(--card2)" onclick="admInfoAdd()">＋ Blok</button><button class="btn" onclick="admInfoSave()">Saqlash</button></div><small style="color:var(--mut);display:block;margin-top:8px">Blok = rasm + uning tagidagi tavsif. Mijoz bularni o'yin sahifasida ko'radi.</small></div>`:""}
  <div class="card"><div class="lbl" style="margin-top:0">YANGI REGION</div><div class="flex" style="gap:10px"><input id="a_nr" placeholder="masalan: CIS, Global, Tojikiston" style="flex:1"><button class="btn" style="width:auto;padding:0 22px" onclick="admRegAdd()">＋</button></div></div>
  <div style="padding:0 0 130px"><button class="btn" style="background:var(--card2);color:#f87171" onclick="admDelGame()">🗑 ${a.auto?"O'yinni o'chirish":"O'yinni o'chirish (yashirish)"}</button></div>
  <div class="buy"><button class="btn" id="a_save" onclick="admSave()">Saqlash${admDirty()?" ●":""}</button></div></div>`}
function admInfoAdd(){S.ad.info.push({img:"",txt:""});render()}
function admInfoRm(i,onlyImg){if(onlyImg)S.ad.info[i].img="";else S.ad.info.splice(i,1);render()}
function admInfoPick(i,inp){const f=inp.files&&inp.files[0];if(!f)return;const rd=new FileReader();
  rd.onload=()=>{const im=new Image();im.onload=()=>{const sc=Math.min(1,900/Math.max(im.width,im.height)),cv=document.createElement("canvas");cv.width=Math.round(im.width*sc);cv.height=Math.round(im.height*sc);
    cv.getContext("2d").drawImage(im,0,0,cv.width,cv.height);S.ad.info[i].img=cv.toDataURL("image/jpeg",.82);render()};im.onerror=()=>alert(t("err"));im.src=rd.result};rd.readAsDataURL(f)}
async function admInfoSave(){const a=S.ad;
  const blocks=(a.info||[]).map(b=>({txt:b.txt||"",img:(b.img||"").startsWith("data:")?b.img:(b.img?"keep:"+((b.img.match(/\/gi\/[^\/]+\/(\d+)/)||[])[1]||"x"):"")}));
  const r=await api("/api/admin/info",{game:a.id,blocks});
  if(r&&r.ok){toast("Saqlandi ✓");S.cat=(await api("/api/catalog"))||S.cat;admLoad(a.id,a.cur,true)}else alert((r&&r.msg)||t("err"))}
async function admDelGame(){const a=S.ad,msg=a.auto?"«"+a.name+"» o'yini butunlay o'chirilsinmi?":"«"+a.name+"» asosiy o'yin, o'chirib bo'lmaydi, lekin mijozlardan yashiriladi. Davom etasizmi?";
  const go2=async ok=>{if(!ok)return;const r=await api("/api/admin/save",{game:a.id,del_game:true});
    if(r&&r.ok){toast(r.deleted?"O'chirildi":"Yashirildi");S.cat=(await api("/api/catalog"))||S.cat;admOpen()}else alert(t("err"))};
  if(tg&&tg.showConfirm)tg.showConfirm(msg,go2);else go2(confirm(msg))}
async function admSave(){const a=S.ad,b=$("#a_save");if(b)b.disabled=true;
  const ren=admRenPending(),map={};
  if(ren.length){const r0=await api("/api/admin/save",{game:a.id,tabren:ren});
    if(!(r0&&r0.ok)){if(b)b.disabled=false;return alert((r0&&r0.msg)||t("err"))}
    ren.forEach(x=>map[x.from]=x.to)}
  const edits=Object.entries(a.ed).map(([id,e])=>({id,...e,...(e.tab&&map[e.tab]?{tab:map[e.tab]}:{})}));
  const adds=a.adds.map(x=>({region:x.region,tab:map[x.tab]||x.tab,name:x.name,price:x.price,sku:x.sku,hidden:!!x.hidden}));
  const regions=admRegs().filter(r=>r.fresh||a.rg[r.region]).map(r=>({region:r.region,title:r.title||"",hidden:!!r.hidden}));
  const r=await api("/api/admin/save",{game:a.id,edits,adds,dels:a.dels.map(x=>x.slice(1)),regions,hide_game:!!a.hide});
  if(r&&r.ok){toast("Saqlandi ✓");S.cat=(await api("/api/catalog"))||S.cat;admLoad(a.id,a.cur,true)}else{if(b)b.disabled=false;alert((r&&r.msg)||t("err"))}}
function hist(){const H=S.hist,tab=S.htab||"orders";
  const head=`<div class="flex" style="align-items:center;justify-content:space-between;margin:10px 0 18px"><h1>${t("history")}</h1><div class="av" style="background:var(--card);border:1px solid var(--line);color:var(--tx)" onclick="refreshHist()">${I("refresh",22)}</div></div>
  <div class="seg" style="margin:0 0 16px"><a class="${tab=="orders"?"on":""}" onclick="setH('htab','orders')">${t("orders")}</a><a class="${tab=="fin"?"on":""}" onclick="setH('htab','fin')">${t("finance")}</a></div>`;
  const chips=(arr,key,cur)=>`<div class="reg chips" style="margin:0 0 14px">${arr.map(([k,n])=>`<a class="${cur==k?"on":""}" onclick="setH('${key}','${k}')">${t(n)}</a>`).join("")}</div>`;
  const none=`<p style="color:var(--mut);text-align:center;margin-top:40px">—</p>`;
  if(tab=="orders"){const f=S.hf||"all";
    const rows=H.orders.filter(x=>f=="all"||x.status==f||(f=="pending"&&x.status=="processing")).map(x=>{const g=gid(x.game);return `<div class="oc"><div class="oi">${g?pi(g):""}${x.game?ini(x.game):"🛒"}</div><div style="flex:1;min-width:0"><b class="tr">${esc(x.item||x.title)}</b><div class="sm">${esc(x.game||"")} · ${x.date}</div><div class="sm2">#${x.id}</div></div><div style="text-align:right;flex:none"><b>${fmt(x.price)} ${t("cur")}</b><br><span class="bd ${x.status}">${t(ST[x.status]||"st_wait")}</span></div></div>`}).join("");
    return head+chips([["all","st_all"],["done","st_done"],["pending","st_wait"],["cancelled","st_cancel"]],"hf",f)+(rows||none)}
  const inc=H.fin.filter(x=>x.amount>0).reduce((a,x)=>a+x.amount,0),exp=H.fin.filter(x=>x.amount<0).reduce((a,x)=>a-x.amount,0),f=S.ff||"all";
  const sum=(ic,col,lb,val,sg)=>`<div class="card" style="margin:0"><div class="sm" style="color:${col};display:flex;gap:6px;align-items:center;margin:0">${I(ic,18)}${t(lb)}</div><div style="font-size:28px;font-weight:800;color:${col};margin:10px 0 2px">${sg}${fmt(val)}</div><small style="color:var(--mut)">${t("cur")}</small></div>`;
  const rows=H.fin.filter(x=>f=="all"||(f=="in"?x.amount>0:x.amount<0)).map(x=>{const pos=x.amount>0,ti=x.title=="Top up"?t("fin_topup"):x.title=="Referral bonus"?t("fin_ref"):x.title=="Refund"?t("fin_refund"):x.title;
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
  const rows=[["uplus","#12302a","#22c993","invite","go('friends')"],["bell","#33290f","#facc15","notif","note()"],["chat","#12303a","#38bdf8","support","sup()"],["star","#33290f","#facc15","reviews","openReviews()"],["shield","#1d2347","#8b7bff","security","sec()"]].concat(S.u.admin?[["tools","#2a2150","#a78bfa","!Admin panel (narx va mahsulotlar)","admOpen()"]]:[]).map(([ic,bg,col,k,fn])=>`<div class="mr" onclick="${fn}"><div class="ti" style="background:${bg};color:${col}">${I(ic,22)}</div><b>${k[0]=="!"?k.slice(1):t(k)}</b><span class="chv">${I("chev",20)}</span></div>`).join("");
  return `<h1 style="margin:10px 0 16px">${t("profile")}</h1>
  <div class="card" style="background:linear-gradient(160deg,#171a33,#0d0f1c);padding:22px"><div class="flex" style="align-items:center;gap:16px;margin-bottom:18px"><div class="ring"><div>${av}</div></div><div style="min-width:0"><b style="font-size:20px">${nm}</b><br><small style="color:var(--mut)">${tu.username?"@"+esc(tu.username):""}</small><div class="chip" onclick="cp(${tu.id||0})">ID: ${tu.id||""} ${I("copy",14)}</div></div></div>
  <div class="flex" style="margin-bottom:16px">${mini("balance",u.balance,"var(--tx)")}${mini("spent",u.spent,"#f59a0b")}</div><button class="btn" style="background:#3b3399" onclick="go('topup')">${t("topup")}</button></div>
  <div class="card" style="padding:0"><div class="mr" style="border:0;padding-bottom:12px"><div class="ti" style="background:#12303a;color:#38bdf8">${I("globe",22)}</div><b>${t("lang")}</b></div><div style="padding:0 16px 16px"><div class="seg" style="margin:0">${[["uz","O'zbek"],["tg","Тоҷикӣ"],["ru","Русский"],["en","English"]].map(([k,n])=>`<a class="${LANG==k?"on":""}" onclick="chLang('${k}')">${n}</a>`).join("")}</div></div>
  <div class="mr" style="border-top:1px solid var(--line);border-bottom:0" onclick="document.body.classList.toggle('light');localStorage.setItem('light',document.body.classList.contains('light')?1:'');render()"><div class="ti" style="background:#1d2347;color:#8b7bff">${I("moon",22)}</div><b>${t("night")}</b><div class="sw ${light?"off":""}"></div></div></div>
  <div class="card" style="padding:0">${rows}</div>`}
async function openTop(k){S.tk=k;S.tp="week";await loadTop()}
async function loadTop(){const r=await api(`/api/top?kind=${S.tk}&period=${S.tp}`);S.top=(r&&r.items)||[];go("top")}
function topv(){const T=S.top||[],tp=S.tp||"week";
  const rows=T.map((x,i)=>{const m=["🥇","🥈","🥉"][i];return `<div class="rk ${i<3?"gold":""}"><span style="width:34px;text-align:center;font-size:${m?22:16}px;color:var(--mut);font-weight:700">${m||i+1}</span><div class="av" style="position:relative;width:52px;height:52px;background:hsl(${((x.name||"?").charCodeAt(0)||0)*37%360} 55% 42%)">${ini(x.name)}${avi(x.av)}</div><b class="tr" style="flex:1">${esc(x.name)}</b><b style="flex:none">${fmt(x.total)} TJS</b></div>`}).join("");
  return `<div class="flex" style="align-items:center;gap:14px;margin:8px 0 18px"><div class="av" style="background:var(--card);border:1px solid var(--line);color:var(--tx);width:48px;height:48px" onclick="go('friends')">${I("back",22)}</div><h1>${t(S.tk=="donors"?"top_donors":"top_topups")}</h1></div>
  <div class="seg" style="margin:0 0 16px">${[["week","week"],["month","month"],["all","alltime"]].map(([k,n])=>`<a class="${tp==k?"on":""}" onclick="S.tp='${k}';loadTop()">${t(n)}</a>`).join("")}</div>${rows||`<p style="color:var(--mut);text-align:center;margin-top:40px">${t("no_data")}</p>`}`}
async function chLang(l){await setLang(l);api("/api/lang",{lang:l});render()}
init();
