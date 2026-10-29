import asyncio, base64, hmac, hashlib, json, time
from urllib.parse import parse_qsl
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import (Message, CallbackQuery, InlineKeyboardMarkup,
                           InlineKeyboardButton, WebAppInfo, BufferedInputFile)
import config as C, database as D

import os
HERE = os.path.dirname(os.path.abspath(__file__))
bot = Bot(C.BOT_TOKEN); dp = Dispatcher()

# ---------- BOT ----------
@dp.message(CommandStart())
async def start(m: Message, command: CommandObject):
    D.user(m.from_user.id, m.from_user.full_name, command.args)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🎮 Open", web_app=WebAppInfo(url=C.MINIAPP_URL))]])
    await m.answer("Donat 🎮", reply_markup=kb)

@dp.message(F.photo)  # mijoz chek yuboradi -> adminga
async def receipt(m: Message):
    t = D.q("SELECT id FROM topups WHERE uid=? AND status='pending' ORDER BY id DESC", (m.from_user.id,)).fetchone()
    if not t: return await m.answer("—")
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅", callback_data=f"ok{t['id']}"),
        InlineKeyboardButton(text="❌", callback_data=f"no{t['id']}")]])
    await m.copy_to(C.ADMIN_ID, caption=f"Top up #{t['id']} от {m.from_user.id}", reply_markup=kb)
    await m.answer("✅ Chek qabul qilindi / Чек получен")

@dp.callback_query(F.data.regexp(r"^(ok|no)\d+$"))
async def decide(c: CallbackQuery):
    if c.from_user.id != C.ADMIN_ID: return await c.answer()
    tid = int(c.data[2:])
    if c.data.startswith("ok"):
        t = D.approve_topup(tid, C.REF_PERCENT)
        if t: await bot.send_message(t["uid"], f"✅ +{t['amount']}")
    else:
        D.q("UPDATE topups SET status='rejected' WHERE id=? AND status='pending'", (tid,))
    await c.message.edit_reply_markup(); await c.answer("OK")

@dp.callback_query(F.data.startswith("done"))
async def done(c: CallbackQuery):
    if c.from_user.id != C.ADMIN_ID: return await c.answer()
    oid = int(c.data[4:]); D.q("UPDATE orders SET status='done' WHERE id=?", (oid,))
    o = D.q("SELECT uid FROM orders WHERE id=?", (oid,)).fetchone()
    await bot.send_message(o["uid"], f"✅ Order #{oid}")
    await c.message.edit_reply_markup(); await c.answer("OK")

# ---------- API ----------
def check_init(raw: str):
    """Telegram initData imzosini tekshiradi (soxta so'rovlardan himoya)."""
    try:
        d = dict(parse_qsl(raw, keep_blank_values=True)); h = d.pop("hash")
        s = "\n".join(f"{k}={v}" for k, v in sorted(d.items()))
        key = hmac.new(b"WebAppData", C.BOT_TOKEN.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(hmac.new(key, s.encode(), hashlib.sha256).hexdigest(), h): return None
        if time.time() - int(d["auth_date"]) > 86400: return None
        return json.loads(d["user"])
    except Exception: return None

hits = {}
@web.middleware
async def mw(req, handler):
    if req.method == "OPTIONS": r = web.Response()
    else:
        if req.path.startswith("/api/") and req.path != "/api/catalog":
            u = check_init(req.headers.get("X-Init", ""))
            if not u: return web.json_response({"error": "auth"}, status=401, headers=cors())
            req["u"] = D.user(u["id"], u.get("first_name", ""))
            k = u["id"]; now = time.time()  # rate limit: 30 so'rov/daqiqa
            hits[k] = [x for x in hits.get(k, []) if now - x < 60] + [now]
            if len(hits[k]) > 30: return web.json_response({"error": "rate"}, status=429, headers=cors())
        r = await handler(req)
    r.headers.update(cors()); return r
def cors(): return {"Access-Control-Allow-Origin": C.ORIGIN, "Access-Control-Allow-Headers": "Content-Type,X-Init", "Access-Control-Allow-Methods": "GET,POST,OPTIONS"}

async def catalog(r): return web.json_response({**C.CATALOG, "bot": (await bot.me()).username, "support": C.SUPPORT, "rate": C.RATE, "pay": [{k: x[k] for k in ("id", "name", "type", "cur", "color", "icon")} for x in C.PAY]})
async def me(r):
    u = r["u"]; n = D.q("SELECT COUNT(*) c FROM users WHERE invited_by=?", (u["id"],)).fetchone()["c"]
    b = D.q("SELECT COUNT(*) c FROM users WHERE invited_by=? AND paid=1", (u["id"],)).fetchone()["c"]
    return web.json_response({"balance": round(u["balance"], 2), "spent": round(u["spent"], 2), "lang": u["lang"], "ref": u["ref"], "refs": n, "buyers": b, "bonus": round(u["bonus"], 2)})
async def lang(r):
    l = (await r.json()).get("lang")
    if l in ("ru", "uz", "tg", "en"): D.q("UPDATE users SET lang=? WHERE id=?", (l, r["u"]["id"]))
    return web.json_response({"ok": True})
async def order(r):
    d = await r.json(); g, i = C.find_item(d.get("game"), d.get("item"))
    pid = str(d.get("pid", ""))
    if not i or not pid.isdigit(): return web.json_response({"error": "bad"})
    title = f"{g['name']} {i['name']}" + (f" [{d.get('region')}]" if g.get("regions") else "")
    oid = D.buy(r["u"]["id"], title, pid, i["price"])  # narx serverdan olinadi
    if not oid: return web.json_response({"error": "funds"})
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Done", callback_data=f"done{oid}")]])
    await bot.send_message(C.ADMIN_ID, f"🛒 #{oid}\n{title}\nID: {pid}\nUser: {r['u']['id']}", reply_markup=kb)
    return web.json_response({"ok": True, "balance": round(D.user(r["u"]["id"])["balance"], 2)})
async def topup(r):
    d = await r.json()
    try: a = float(d.get("amount", 0))
    except Exception: a = 0
    x = next((p for p in C.PAY if p["id"] == d.get("method")), None)
    if not x or not 10 <= a <= 5000: return web.json_response({"error": "bad"})
    tid = D.q("INSERT INTO topups(uid,amount) VALUES(?,?)", (r["u"]["id"], a)).lastrowid
    pa = a if x["cur"] == "TJS" else round(a / C.RATE)
    return web.json_response({"ok": True, "id": tid, "amount": a, "pay": pa, "cur": x["cur"], "type": x["type"], "value": x["value"], "holder": x["holder"], "name": x["name"], "icon": x["icon"], "color": x["color"], "method": x["id"]})
async def receipt_api(r):
    d = await r.json(); uid = r["u"]["id"]
    t = D.q("SELECT * FROM topups WHERE id=? AND uid=? AND status='pending'", (d.get("id"), uid)).fetchone()
    try: raw = base64.b64decode(str(d.get("image", "")).split(",")[-1], validate=True)
    except Exception: raw = b""
    if not t or not 1000 < len(raw) < 6_000_000 or not (raw[:3] == b"\xff\xd8\xff" or raw[:4] == b"\x89PNG"):
        return web.json_response({"error": "bad"})
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅", callback_data=f"ok{t['id']}"), InlineKeyboardButton(text="❌", callback_data=f"no{t['id']}")]])
    await bot.send_photo(C.ADMIN_ID, BufferedInputFile(raw, "receipt.jpg"), caption=f"💳 Top up #{t['id']}\nUser: {uid}\n{t['amount']} TJS\nMethod: {str(d.get('method', ''))[:20]}", reply_markup=kb)
    return web.json_response({"ok": True})
async def history(r):
    uid = r["u"]["id"]; f = lambda x: str(x)[:16]
    o = [{"id": x["id"], "title": x["title"], "price": x["price"], "status": x["status"], "date": f(x["ts"])} for x in D.q("SELECT * FROM orders WHERE uid=? ORDER BY id DESC LIMIT 50", (uid,))]
    n = [{"title": x["title"], "amount": x["amount"], "date": f(x["ts"])} for x in D.q("SELECT * FROM fin WHERE uid=? ORDER BY id DESC LIMIT 50", (uid,))]
    return web.json_response({"orders": o, "fin": n})

def _img(path):
    async def h(r):
        return web.FileResponse(path) if os.path.exists(path) else web.Response(status=404)
    return h
async def main():
    app = web.Application(middlewares=[mw], client_max_size=8 * 1024 * 1024)
    app.add_routes([web.get("/api/catalog", catalog), web.get("/api/me", me), web.post("/api/lang", lang), web.post("/api/order", order),
                    web.post("/api/topup", topup), web.post("/api/receipt", receipt_api), web.get("/api/history", history), web.route("OPTIONS", "/{p:.*}", lambda r: web.Response()),
                    web.get("/", lambda r: web.FileResponse(os.path.join(HERE, "index.html")))])
    for f in ("style.css", "app.js", "i18n.js", "ru.json", "uz.json", "tg.json", "en.json", "logo.png", "splash.jpg"):
        app.router.add_get("/" + f, lambda r, f=f: web.FileResponse(os.path.join(HERE, f)))
    for g in C.CATALOG["games"]:
        app.router.add_get("/" + g["id"] + ".png", _img(os.path.join(HERE, g["id"] + ".png")))
    run = web.AppRunner(app); await run.setup(); await web.TCPSite(run, "0.0.0.0", C.PORT).start()
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())
