import html as H
import json as _json, urllib.request, urllib.error, urllib.parse
import re, math, hashlib
import receipt_ai as AI
from datetime import datetime, timezone, timedelta
import logging
logging.basicConfig(level=logging.INFO)
import asyncio, base64, hmac, hashlib, json, time
from urllib.parse import parse_qsl
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import (Message, CallbackQuery, InlineKeyboardMarkup,
                           InlineKeyboardButton, WebAppInfo, BufferedInputFile, FSInputFile)
import config as C, database as D, donatix as DX

# Baza tuzilmasini o'zi tekshiradi (database.py eski bo'lsa ham ishlayveradi)
for _s in ("CREATE TABLE IF NOT EXISTS ratings(oid INTEGER PRIMARY KEY,uid INTEGER,stars INTEGER)",
           "ALTER TABLE users ADD COLUMN lang_set INTEGER DEFAULT 0",
           "ALTER TABLE orders ADD COLUMN game TEXT DEFAULT ''",
           "ALTER TABLE orders ADD COLUMN item TEXT DEFAULT ''",
           "ALTER TABLE ratings ADD COLUMN text TEXT DEFAULT ''",
           "ALTER TABLE ratings ADD COLUMN reply TEXT DEFAULT ''",
           "ALTER TABLE ratings ADD COLUMN ts TEXT",
           "ALTER TABLE orders ADD COLUMN dx_fields TEXT DEFAULT ''",
           "ALTER TABLE orders ADD COLUMN qty INTEGER DEFAULT 1",
           "CREATE TABLE IF NOT EXISTS dxcat(product_id TEXT PRIMARY KEY,game_id TEXT,region TEXT,region_title TEXT,name TEXT,tab TEXT,emoji TEXT,price_usd REAL,fields TEXT,kind TEXT,sort INTEGER,qmin INTEGER,qmax INTEGER,active INTEGER DEFAULT 1)",
           "CREATE TABLE IF NOT EXISTS dxgames(game_id TEXT PRIMARY KEY,cat TEXT,q TEXT)",
           "CREATE TABLE IF NOT EXISTS rhash(h TEXT PRIMARY KEY,tid INTEGER)",
           "CREATE TABLE IF NOT EXISTS dxmap(item_id TEXT,region TEXT,product_id TEXT,PRIMARY KEY(item_id,region))",
           "ALTER TABLE orders ADD COLUMN dx_id TEXT DEFAULT ''",
           "ALTER TABLE orders ADD COLUMN nick TEXT DEFAULT ''",
           "ALTER TABLE topups ADD COLUMN method TEXT DEFAULT ''",
           "UPDATE topups SET status='expired' WHERE status='pending' AND (method IS NULL OR method='')"):
    try: D.q(_s)
    except Exception: pass


import os
HERE = os.path.dirname(os.path.abspath(__file__))
bot = Bot(C.BOT_TOKEN); dp = Dispatcher()

# ---------- BOT ----------
PICK = "🌐 Tilni tanlang · Выберите язык · Забонро интихоб кунед · Choose language"
W = {
 "tg": dict(text="👋 <b>Хуш омадед ба Diavex Shop!</b>\n\n🎮 Донат барои бозиҳои дӯстдоштаатон: зуд, арзон ва бехатар.\n\n✨ Бо мо хеле қулай аст!\n\n🙏 Ташаккур, ки моро интихоб кардед!", shop="🛍 Оғози харид", les="🎬 Дарсҳо", ord="📝 Фармоишҳо", chan="📢 Канали хабарҳо", lang="🌐 Забон", sup="💬 Дастгирӣ"),
 "ru": dict(text="👋 <b>Добро пожаловать в Diavex Shop!</b>\n\n🎮 Донат для ваших любимых игр: быстро, выгодно и безопасно.\n\n✨ С нами удобно!\n\n🙏 Спасибо, что выбрали нас!", shop="🛍 Начать покупки", les="🎬 Уроки", ord="📝 Заказы", chan="📢 Канал новостей", lang="🌐 Язык", sup="💬 Поддержка"),
 "uz": dict(text="👋 <b>Diavex Shop'ga xush kelibsiz!</b>\n\n🎮 Sevimli o'yinlaringiz uchun donat: tez, arzon va xavfsiz.\n\n✨ Biz bilan juda qulay!\n\n🙏 Bizni tanlaganingiz uchun rahmat!", shop="🛍 Xaridni boshlash", les="🎬 Darslar", ord="📝 Buyurtmalar", chan="📢 Yangiliklar kanali", lang="🌐 Til", sup="💬 Yordam"),
 "en": dict(text="👋 <b>Welcome to Diavex Shop!</b>\n\n🎮 Top-ups for your favorite games: fast, affordable and safe.\n\n✨ It's easy with us!\n\n🙏 Thank you for choosing us!", shop="🛍 Start shopping", les="🎬 Tutorials", ord="📝 Orders", chan="📢 News channel", lang="🌐 Language", sup="💬 Support"),
}
FID = {}
def picker():
    b = lambda t, l: InlineKeyboardButton(text=t, callback_data="lg_" + l)
    return InlineKeyboardMarkup(inline_keyboard=[[b("🇺🇿 O'zbekcha", "uz"), b("🇹🇯 Тоҷикӣ", "tg")], [b("🇷🇺 Русский", "ru"), b("🇬🇧 English", "en")]])

def _kb(w):
    url = (C.MINIAPP_URL or "").strip(); ok = url.startswith("https://")
    rows = []
    if ok: rows.append([InlineKeyboardButton(text=w["shop"], web_app=WebAppInfo(url=url))])
    r = []
    if C.LESSONS_URL.startswith("http"): r.append(InlineKeyboardButton(text=w["les"], url=C.LESSONS_URL))
    if ok: r.append(InlineKeyboardButton(text=w["ord"], web_app=WebAppInfo(url=url.rstrip("/") + "/?go=hist")))
    if r: rows.append(r)
    if C.CHANNEL_URL.startswith("http"): rows.append([InlineKeyboardButton(text=w["chan"], url=C.CHANNEL_URL)])
    r = [InlineKeyboardButton(text=w["lang"], callback_data="chlang")]
    sup = (C.SUPPORT or "").strip().lstrip("@")
    if sup: r.append(InlineKeyboardButton(text=w["sup"], url=f"https://t.me/{sup}"))
    rows.append(r)
    return InlineKeyboardMarkup(inline_keyboard=rows)

async def welcome(chat_id, l):
    l = l if l in W else "ru"; w = W[l]; kb = _kb(w)
    try:
        msg = await bot.send_photo(chat_id, FID.get(l) or FSInputFile(os.path.join(HERE, f"welcome_{l}.jpg")), caption=w["text"], parse_mode="HTML", reply_markup=kb)
        FID[l] = msg.photo[-1].file_id
    except Exception:
        logging.exception("welcome: photo failed")
        try:
            await bot.send_message(chat_id, w["text"], parse_mode="HTML", reply_markup=kb)
        except Exception:
            logging.exception("welcome: keyboard failed")
            await bot.send_message(chat_id, w["text"], parse_mode="HTML")

@dp.message(CommandStart())
async def start(m: Message, command: CommandObject):
    u = D.user(m.from_user.id, m.from_user.full_name, command.args)
    if u["lang_set"]: await welcome(m.chat.id, u["lang"])
    else: await m.answer(PICK, reply_markup=picker())

@dp.message(Command("lang"))
async def lang_cmd(m: Message):
    D.user(m.from_user.id, m.from_user.full_name)
    await m.answer(PICK, reply_markup=picker())

@dp.callback_query(F.data == "chlang")
async def chlang(c: CallbackQuery):
    await c.message.answer(PICK, reply_markup=picker()); await c.answer()

@dp.callback_query(F.data.regexp(r"^lg_(uz|tg|ru|en)$"))
async def pick_lang(c: CallbackQuery):
    l = c.data[3:]
    D.user(c.from_user.id, c.from_user.full_name)
    D.q("UPDATE users SET lang=?, lang_set=1 WHERE id=?", (l, c.from_user.id))
    await c.answer()
    try: await c.message.delete()
    except Exception: pass
    await welcome(c.from_user.id, l)

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
    tid = int(c.data[2:]); okay = c.data.startswith("ok"); done = False
    if okay:
        t = D.approve_topup(tid, C.REF_PERCENT)
        if t: done = True; await tell(t["uid"], "okd", amt=f"{t['amount']:.2f}", no=tid)
    else:
        t = D.q("SELECT * FROM topups WHERE id=? AND status='pending'", (tid,)).fetchone()
        if t and D.q("UPDATE topups SET status='rejected' WHERE id=? AND status='pending'", (tid,)).rowcount:
            done = True; await tell(t["uid"], "rej", no=tid)
    try:
        if done: await c.message.edit_caption(caption=(c.message.html_text or "") + ("\n\n✅ <b>Tasdiqlandi</b>" if okay else "\n\n❌ <b>Rad etildi</b>"), parse_mode="HTML")
        else: await c.message.edit_reply_markup()
    except Exception: pass
    await c.answer("OK" if done else "—")

import html as H
CUR = {"ru": "сомони", "uz": "somoni", "tg": "сомонӣ", "en": "TJS"}
LINE = "━━━━━━━━━━━━━━━━━━"
T = {
 "tg": dict(
  acc="✅ <b>Фармоиши шумо қабул шуд!</b>\n\n📦 Маҳсулот: <b>{item}</b>\n🆔 ID: {pid}\n🏷 Фармоиш: #{oid}\n\n⏳ Иҷро мешавад, лутфан интизор шавед.\nТайёр шуд, хабар мефиристем! 🎮",
  done="🎉 <b>Фармоиши шумо иҷро шуд!</b>\n" + LINE + "\n🎮 Бозӣ: <b>{game}</b>\n📦 Маҳсулот: <b>{item}</b>\n🆔 ID бозингар: {pid}{nick}\n💰 Пардохт шуд: <b>{price} {cur}</b>\n🏷 Фармоиш: <b>#{oid}</b>\n" + LINE + "\n\nТашаккур барои харид! 🙏\n\n⭐ <b>Хизматро баҳо диҳед:</b>",
  nick="\n🎭 Никнейм: <b>{v}</b>", thx="Ташаккур барои баҳо! {s}"),
 "ru": dict(
  acc="✅ <b>Ваш заказ принят!</b>\n\n📦 Товар: <b>{item}</b>\n🆔 ID: {pid}\n🏷 Заказ: #{oid}\n\n⏳ Выполняется, пожалуйста, подождите.\nКак только будет готово — сообщим! 🎮",
  done="🎉 <b>Ваш заказ выполнен!</b>\n" + LINE + "\n🎮 Игра: <b>{game}</b>\n📦 Товар: <b>{item}</b>\n🆔 ID игрока: {pid}{nick}\n💰 Оплачено: <b>{price} {cur}</b>\n🏷 Заказ: <b>#{oid}</b>\n" + LINE + "\n\nСпасибо за покупку! 🙏\n\n⭐ <b>Оцените сервис:</b>",
  nick="\n🎭 Никнейм: <b>{v}</b>", thx="Спасибо за оценку! {s}"),
 "uz": dict(
  acc="✅ <b>Buyurtmangiz qabul qilindi!</b>\n\n📦 Mahsulot: <b>{item}</b>\n🆔 ID: {pid}\n🏷 Buyurtma: #{oid}\n\n⏳ Bajarilmoqda, iltimos kuting.\nTayyor bo'lgach, xabar beramiz! 🎮",
  done="🎉 <b>Buyurtmangiz bajarildi!</b>\n" + LINE + "\n🎮 O'yin: <b>{game}</b>\n📦 Mahsulot: <b>{item}</b>\n🆔 O'yinchi ID: {pid}{nick}\n💰 To'landi: <b>{price} {cur}</b>\n🏷 Buyurtma: <b>#{oid}</b>\n" + LINE + "\n\nXaridingiz uchun rahmat! 🙏\n\n⭐ <b>Xizmatni baholang:</b>",
  nick="\n🎭 Nikneym: <b>{v}</b>", thx="Bahoyingiz uchun rahmat! {s}"),
 "en": dict(
  acc="✅ <b>Your order has been accepted!</b>\n\n📦 Product: <b>{item}</b>\n🆔 ID: {pid}\n🏷 Order: #{oid}\n\n⏳ In progress, please wait.\nWe will notify you when it is ready! 🎮",
  done="🎉 <b>Your order is complete!</b>\n" + LINE + "\n🎮 Game: <b>{game}</b>\n📦 Product: <b>{item}</b>\n🆔 Player ID: {pid}{nick}\n💰 Paid: <b>{price} {cur}</b>\n🏷 Order: <b>#{oid}</b>\n" + LINE + "\n\nThank you for your purchase! 🙏\n\n⭐ <b>Rate our service:</b>",
  nick="\n🎭 Nickname: <b>{v}</b>", thx="Thanks for rating! {s}"),
}
_T2 = {
 "tg": dict(wr="💬 Шарҳ навиштан", ask="💬 <b>Шарҳи худро нависед:</b>\n\nФикри худро дар бораи хизматрасонӣ нависед ва фиристед.\n\nБекор кардан: /cancel", got="✅ <b>Ташаккур барои шарҳатон!</b>\n\nФикри шумо барои мо хеле муҳим аст. 🙏", rep="💬 <b>Ба шарҳи шумо ҷавоб доданд</b>\n«{q}»\n\n🛡 <b>Diavex Shop:</b> {a}", canc="Бекор карда шуд."),
 "ru": dict(wr="💬 Написать отзыв", ask="💬 <b>Напишите отзыв:</b>\n\nНапишите ваше мнение о нашем сервисе и отправьте.\n\nОтмена: /cancel", got="✅ <b>Спасибо за отзыв!</b>\n\nВаше мнение очень важно для нас. 🙏", rep="💬 <b>На ваш отзыв ответили</b>\n«{q}»\n\n🛡 <b>Diavex Shop:</b> {a}", canc="Отменено."),
 "uz": dict(wr="💬 Sharh yozish", ask="💬 <b>Sharhingizni yozing:</b>\n\nXizmatimiz haqida fikringizni yozib yuboring.\n\nBekor qilish: /cancel", got="✅ <b>Sharhingiz uchun rahmat!</b>\n\nSizning fikringiz biz uchun juda muhim. 🙏", rep="💬 <b>Sharhingizga javob berishdi</b>\n«{q}»\n\n🛡 <b>Diavex Shop:</b> {a}", canc="Bekor qilindi."),
 "en": dict(wr="💬 Write a review", ask="💬 <b>Write your review:</b>\n\nTell us what you think about our service and send it.\n\nCancel: /cancel", got="✅ <b>Thank you for your review!</b>\n\nYour opinion is very important to us. 🙏", rep="💬 <b>Your review received a reply</b>\n«{q}»\n\n🛡 <b>Diavex Shop:</b> {a}", canc="Cancelled."),
}
for _l, _d in _T2.items(): T[_l].update(_d)
_T3 = {
 "tg": dict(rcv="⏳ <b>Пардохти шумо қабул шуд!</b>\n\n💵 Маблағ: <b>{amt} сомонӣ</b>\n🏦 Усул: <b>{method}</b>\n🔢 Дархост #: {no}\n\nСистема тафтишотро анҷом медиҳад, маблағ ба зудӣ ба балансатон илова мешавад ✅",
  okd="✅ <b>Пардохти шумо тасдиқ шуд!</b>\n\n💰 <b>+{amt} сомонӣ</b> ба балансатон илова шуд.\n🆔 Депозит: #{no}",
  rej="❌ <b>Пардохти шумо рад карда шуд.</b>\n\n🔢 Дархост #: {no}\nАгар хато шуда бошад, ба дастгирӣ нависед.", kind_phone="Телефон", kind_card="Корт"),
 "ru": dict(rcv="⏳ <b>Ваш платёж принят!</b>\n\n💵 Сумма: <b>{amt} сомони</b>\n🏦 Способ: <b>{method}</b>\n🔢 Заявка #: {no}\n\nСистема проверяет платёж, сумма скоро поступит на ваш баланс ✅",
  okd="✅ <b>Ваш платёж подтверждён!</b>\n\n💰 <b>+{amt} сомони</b> зачислено на ваш баланс.\n🆔 Депозит: #{no}",
  rej="❌ <b>Ваш платёж отклонён.</b>\n\n🔢 Заявка #: {no}\nЕсли это ошибка, напишите в поддержку.", kind_phone="Телефон", kind_card="Карта"),
 "uz": dict(rcv="⏳ <b>To'lovingiz qabul qilindi!</b>\n\n💵 Summa: <b>{amt} somoni</b>\n🏦 Usul: <b>{method}</b>\n🔢 So'rov #: {no}\n\nTizim tekshiruvni amalga oshiradi, summa tez orada balansingizga qo'shiladi ✅",
  okd="✅ <b>To'lovingiz tasdiqlandi!</b>\n\n💰 <b>+{amt} somoni</b> balansingizga qo'shildi.\n🆔 Depozit: #{no}",
  rej="❌ <b>To'lovingiz rad etildi.</b>\n\n🔢 So'rov #: {no}\nXato bo'lgan bo'lsa, yordamga yozing.", kind_phone="Telefon", kind_card="Karta"),
 "en": dict(rcv="⏳ <b>Your payment has been received!</b>\n\n💵 Amount: <b>{amt} TJS</b>\n🏦 Method: <b>{method}</b>\n🔢 Request #: {no}\n\nThe system is checking it, the amount will be added to your balance shortly ✅",
  okd="✅ <b>Your payment is confirmed!</b>\n\n💰 <b>+{amt} TJS</b> has been added to your balance.\n🆔 Deposit: #{no}",
  rej="❌ <b>Your payment was declined.</b>\n\n🔢 Request #: {no}\nIf this is a mistake, contact support.", kind_phone="Phone", kind_card="Card"),
}
for _l, _d in _T3.items(): T[_l].update(_d)
async def tell(uid, key, **kw):
    try: await bot.send_message(uid, T[lang_of(uid)][key].format(**kw), parse_mode="HTML")
    except Exception: logging.exception("tell failed")
_T4 = {
 "tg": dict(ordrej="❌ <b>Фармоиши шумо рад карда шуд.</b>\n\n🏷 Фармоиш: #{no}\n💰 <b>+{amt} сомонӣ</b> ба балансатон баргардонида шуд.\nАгар хато шуда бошад, ба дастгирӣ нависед."),
 "ru": dict(ordrej="❌ <b>Ваш заказ отклонён.</b>\n\n🏷 Заказ: #{no}\n💰 <b>+{amt} сомони</b> возвращено на ваш баланс.\nЕсли это ошибка, напишите в поддержку."),
 "uz": dict(ordrej="❌ <b>Buyurtmangiz rad etildi.</b>\n\n🏷 Buyurtma: #{no}\n💰 <b>+{amt} somoni</b> balansingizga qaytarildi.\nXato bo'lgan bo'lsa, yordamga yozing."),
 "en": dict(ordrej="❌ <b>Your order was declined.</b>\n\n🏷 Order: #{no}\n💰 <b>+{amt} TJS</b> has been returned to your balance.\nIf this is a mistake, contact support."),
}
for _l, _d in _T4.items(): T[_l].update(_d)
PEND = {}
def shop_kb(l):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=W[l]["shop"], web_app=WebAppInfo(url=C.MINIAPP_URL))]])
def rstats():
    d = {i: 0 for i in range(1, 6)}
    for x in D.q("SELECT stars, COUNT(*) c FROM ratings GROUP BY stars"): d[x["stars"]] = x["c"]
    n = sum(d.values())
    return {"avg": round(sum(k * v for k, v in d.items()) / n, 1) if n else 0, "count": n, "dist": d}

def lang_of(uid):
    u = D.q("SELECT lang FROM users WHERE id=?", (uid,)).fetchone()
    return u["lang"] if u and u["lang"] in T else "ru"
async def notify(uid, kind, o, nick=""):
    nick = nick or (o["nick"] if "nick" in o.keys() else "")
    l = lang_of(uid); t = T[l]; e = H.escape
    nk = t["nick"].format(v=e(nick)) if nick else ""
    text = t[kind].format(item=e(o["item"] or o["title"]), game=e(o["game"] or ""), pid=e(str(o["pid"])), oid=o["id"], price=f"{o['price']:.2f}", cur=CUR[l], nick=nk)
    kb = None
    if kind == "done":
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⭐" * n, callback_data=f"rt{o['id']}_{n}")] for n in range(5, 0, -1)])
    try: await bot.send_message(uid, text, parse_mode="HTML", reply_markup=kb)
    except Exception: pass

@dp.callback_query(F.data.startswith("done"))
async def done(c: CallbackQuery):
    if c.from_user.id != C.ADMIN_ID: return await c.answer()
    oid = int(c.data[4:])
    if D.q("UPDATE orders SET status='done' WHERE id=? AND status='pending'", (oid,)).rowcount:
        o = D.q("SELECT * FROM orders WHERE id=?", (oid,)).fetchone()
        await notify(o["uid"], "done", o)
    await c.message.edit_reply_markup(); await c.answer("OK")

@dp.callback_query(F.data.regexp(r"^rt\d+_[1-5]$"))
async def rate(c: CallbackQuery):
    oid, n = map(int, c.data[2:].split("_"))
    o = D.q("SELECT * FROM orders WHERE id=? AND uid=? AND status='done'", (oid, c.from_user.id)).fetchone()
    if o and D.q("INSERT OR IGNORE INTO ratings(oid,uid,stars,ts) VALUES(?,?,?,datetime('now'))", (oid, c.from_user.id, n)).rowcount:
        t = T[lang_of(c.from_user.id)]
        await c.message.edit_reply_markup()
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t["wr"], callback_data=f"rv{oid}")]])
        await c.message.answer(t["thx"].format(s="⭐" * n), reply_markup=kb)
        await bot.send_message(C.ADMIN_ID, f"⭐ {n}/5 — #{oid}")
    await c.answer()

@dp.callback_query(F.data.regexp(r"^rv\d+$"))
async def rv(c: CallbackQuery):
    oid = int(c.data[2:])
    if D.q("SELECT 1 FROM ratings WHERE oid=? AND uid=? AND text=''", (oid, c.from_user.id)).fetchone():
        PEND[c.from_user.id] = ("u", oid)
        await c.message.edit_reply_markup()
        await c.message.answer(T[lang_of(c.from_user.id)]["ask"], parse_mode="HTML")
    await c.answer()

@dp.callback_query(F.data.regexp(r"^rp\d+$"))
async def rp(c: CallbackQuery):
    if c.from_user.id != C.ADMIN_ID: return await c.answer()
    PEND[C.ADMIN_ID] = ("a", int(c.data[2:]))
    await c.message.answer(f"↩ Reply to review #{c.data[2:]} — send text (or /cancel)")
    await c.answer()

@dp.message(Command("cancel"))
async def cancel(m: Message):
    PEND.pop(m.from_user.id, None)
    await m.answer(T[lang_of(m.from_user.id)]["canc"])

@dp.message(F.text & ~F.text.startswith("/"))
async def text_in(m: Message):
    p = PEND.pop(m.from_user.id, None)
    if not p: return
    kind, oid = p; uid = m.from_user.id; txt = m.text.strip()[:500]
    if kind == "u":
        if D.q("UPDATE ratings SET text=? WHERE oid=? AND uid=? AND text=''", (txt, oid, uid)).rowcount:
            await m.answer(T[lang_of(uid)]["got"], parse_mode="HTML", reply_markup=shop_kb(lang_of(uid)))
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="↩ Reply", callback_data=f"rp{oid}")]])
            await bot.send_message(C.ADMIN_ID, f"💬 #{oid} — {H.escape(m.from_user.full_name)}:\n{H.escape(txt)}", parse_mode="HTML", reply_markup=kb)
    elif uid == C.ADMIN_ID:
        r = D.q("SELECT * FROM ratings WHERE oid=?", (oid,)).fetchone()
        if r:
            D.q("UPDATE ratings SET reply=? WHERE oid=?", (txt, oid))
            l = lang_of(r["uid"])
            try: await bot.send_message(r["uid"], T[l]["rep"].format(q=H.escape(r["text"] or ""), a=H.escape(txt)), parse_mode="HTML", reply_markup=shop_kb(l))
            except Exception: pass
            await m.answer("✅ Sent")

@dp.callback_query(F.data.regexp(r"^(od|or)\d+$"))
async def order_decide(c: CallbackQuery):
    if c.from_user.id != C.ADMIN_ID: return await c.answer()
    oid = int(c.data[2:]); okay = c.data.startswith("od"); done = False
    if okay:
        if D.q("UPDATE orders SET status='done' WHERE id=? AND status='pending'", (oid,)).rowcount:
            o = D.q("SELECT * FROM orders WHERE id=?", (oid,)).fetchone(); done = True; await notify(o["uid"], "done", o)
    else:
        o = D.cancel_order(oid)
        if o: done = True; await tell(o["uid"], "ordrej", no=oid, amt=f"{o['price']:.2f}")
    try:
        if done: await c.message.edit_text((c.message.html_text or "") + ("\n\n✅ <b>Bajarildi</b>" if okay else "\n\n❌ <b>Rad etildi (pul qaytarildi)</b>"), parse_mode="HTML")
        else: await c.message.edit_reply_markup()
    except Exception: pass
    await c.answer("OK" if done else "—")

@dp.message(Command("pending"))
async def pending_cmd(m: Message):
    if m.from_user.id != C.ADMIN_ID: return
    rows = D.q("SELECT o.*, u.name uname FROM orders o JOIN users u ON u.id=o.uid WHERE o.status='pending' ORDER BY o.id LIMIT 20").fetchall()
    n = D.q("SELECT COUNT(*) c FROM topups WHERE status='pending'").fetchone()["c"]
    pr = D.q("SELECT COUNT(*) c FROM orders WHERE status='processing'").fetchone()["c"]
    await m.answer(f"⏳ Kutilayotgan buyurtmalar: {len(rows)}\n🤖 Avto jarayonda: {pr}\n⏳ Kutilayotgan to'lovlar: {n} (ularning cheki o'z xabarida, tugmalari bilan)")
    for o in rows:
        prod = (o["title"] or "")[len(o["game"] or ""):].strip() or (o["item"] or "")
        await m.answer(order_caption(o["id"], o["game"] or "", prod, o["pid"], o["price"], o["uid"], o["uname"] or "—", "—", to_local(o["ts"]), o["nick"] or ""), parse_mode="HTML", reply_markup=order_kb(o["id"]))

async def say_chunks(m, lines):
    buf = ""
    for ln in lines:
        if len(buf) + len(ln) > 3500: await m.answer(buf, parse_mode="HTML"); buf = ""
        buf += ln + "\n"
    if buf: await m.answer(buf, parse_mode="HTML")
def pline(p):
    return f"<code>{H.escape(str(p.get('product_id')))}</code> · {H.escape(str(p.get('category_id', '')))} {H.escape(str(p.get('region', '')))} · {H.escape(str(p.get('name') or p.get('title')))} · ${p.get('price_usd')}"

@dp.message(Command("dx"))
async def dx_cmd(m: Message):
    if m.from_user.id != C.ADMIN_ID: return
    if not DX.enabled(): return await m.answer("Donatix ulanmagan (Render'da DONATIX_KEY yo'q).")
    st, bd = await DX.call("GET", "/balance")
    if st == 200 and bd and bd.get("ok"):
        try: bal_txt = "$%.2f" % float(bd["balance"])
        except Exception: bal_txt = "javob tushunarsiz"
    else:
        bal_txt = f"❌ HTTP {st} {H.escape(DX.err_code(bd))}\n👉 {H.escape(DX.hint(st, DX.err_code(bd)))}"
    pr = D.q("SELECT COUNT(*) c FROM orders WHERE status='processing'").fetchone()["c"]
    await m.answer(f"🤖 Donatix avto: <b>{'yoqilgan' if DXSTATE['on'] else 'to‘xtatilgan'}</b>\n💰 Balans: {bal_txt}\n🔗 Bog'langan mahsulotlar: {D.dx_count()}\n⏳ Jarayondagi buyurtmalar: {pr}\n\n/dxsync · /dxcats · /dxfind matn · /dxcat o'yin kategoriya · /dxpause · /dxresume", parse_mode="HTML")

@dp.message(Command("dxpause"))
async def dx_pause(m: Message):
    if m.from_user.id == C.ADMIN_ID: DXSTATE["on"] = False; await m.answer("⏸ Avto to'xtatildi: hamma buyurtma qo'lda keladi. /dxresume bilan yoqing.")
@dp.message(Command("dxresume"))
async def dx_resume(m: Message):
    if m.from_user.id == C.ADMIN_ID: DXSTATE["on"] = True; await m.answer("▶ Avto yoqildi.")

@dp.message(Command("dxcats"))
async def dx_cats(m: Message, command: CommandObject):
    if m.from_user.id != C.ADMIN_ID or not DX.enabled(): return
    cats = await DX.categories()
    if not cats: return await m.answer("Kategoriyalar olinmadi.\n" + H.escape(DX.last_error_text()))
    f = (command.args or "").strip().lower()
    if f: cats = [c for c in cats if f in str(c.get("category_id") or c.get("id") or "").lower() or f in str(c.get("name") or c.get("title") or "").lower()]
    if not cats: return await m.answer("Mos kategoriya yo'q. Boshqa so'z bilan urinib ko'ring: /dxcats free")
    await say_chunks(m, [f"<code>{H.escape(str(c.get('category_id') or c.get('id')))}</code> — {H.escape(str(c.get('name') or c.get('title') or ''))}" for c in cats[:60]])

@dp.message(Command("dxfind"))
async def dx_find(m: Message, command: CommandObject):
    if m.from_user.id != C.ADMIN_ID or not DX.enabled(): return
    q = (command.args or "").strip()
    if not q: return await m.answer("Ishlatish: /dxfind ff")
    items = await DX.products(q=q, pages=1, limit=60)
    if not items: return await m.answer("Hech narsa topilmadi.\n" + H.escape(DX.last_error_text()), parse_mode="HTML")
    await say_chunks(m, [pline(p) for p in items])

@dp.message(Command("dxset"))
async def dx_set_cmd(m: Message, command: CommandObject):
    if m.from_user.id != C.ADMIN_ID or not DX.enabled(): return
    a = (command.args or "").split()
    if len(a) != 3: return await m.answer("Ishlatish: /dxset item_id REGION product_id\nRegion yo'q bo'lsa - yozing. Misol: /dxset ff0 GLOBAL topup-3f9a1c2b7d")
    item_id, rg, sku = a[0], ("" if a[1] == "-" else a[1].upper()), a[2]
    if not any(it["id"] == item_id for g in C.CATALOG["games"] for items in g["tabs"].values() for it in items):
        return await m.answer("❌ Bunday item_id yo'q (catalog.json dagi id, masalan ff0, pu1).")
    p = await DX.product(sku, fresh=True)
    if not p: return await m.answer("❌ Donatix'da bunday product_id topilmadi.")
    D.dx_set(item_id, rg, sku)
    await m.answer(f"✅ {item_id} [{rg or '—'}] → {H.escape(str(p.get('name') or p.get('title')))} (${p.get('price_usd')})", parse_mode="HTML")

@dp.message(Command("dxauto"))
async def dx_auto(m: Message, command: CommandObject):
    if m.from_user.id != C.ADMIN_ID or not DX.enabled(): return
    a = (command.args or "").split()
    g = next((x for x in C.CATALOG["games"] if a and x["id"] == a[0]), None)
    if not g: return await m.answer("Ishlatish: /dxauto o'yin_id [kategoriya_id]\nO'yinlar: " + ", ".join(x["id"] for x in C.CATALOG["games"]))
    cat = a[1] if len(a) > 1 else C.DX_CATEGORIES.get(g["id"])
    prods = await DX.products(category=cat)
    if not prods:   # kategoriya id noto'g'ri bo'lsa, qidiruv orqali topamiz
        found = await DX.products(q=(a[1] if len(a) > 1 else C.DX_QUERIES.get(g["id"], g["name"])))
        cats = sorted({str(p.get("category_id")) for p in found})
        if len(cats) == 1: prods = found
        elif cats: return await m.answer("Bir nechta kategoriya topildi:\n" + "\n".join(cats[:25]) + f"\n\nBittasini tanlab yozing: /dxauto {g['id']} kategoriya_id")
    if not prods: return await m.answer("Mahsulot topilmadi. /dxcats ff kabi yozib kategoriya idsini toping.\n" + H.escape(DX.last_error_text()), parse_mode="HTML")
    def qty(p):
        mm = re.search(r"\d+", str(p.get("name") or p.get("title") or "")); return int(mm.group()) if mm else None
    idx = {}
    for p in prods: idx.setdefault((str(p.get("region") or "").upper(), qty(p)), p)
    ok = 0; miss = []
    for items in g["tabs"].values():
        for it in items:
            mm = re.match(r"\s*(\d+)", it["name"])
            if not mm: miss.append(f"{it['id']} ({it['name']})"); continue
            n = int(mm.group(1))
            for rg in (g.get("regions") or [""]):
                p = idx.get((rg.upper(), n)) or (next((v for (r_, q_), v in idx.items() if q_ == n), None) if rg == "" else None)
                if p and p.get("product_id"): D.dx_set(it["id"], rg, p["product_id"]); ok += 1
                else: miss.append(f"{it['id']} {rg}".strip())
    await m.answer(f"✅ Bog'landi: {ok}\n❌ Topilmadi: {len(miss)}\n" + ", ".join(miss[:50]) + "\n\nTopilmaganlarni /dxfind va /dxset bilan qo'lda bog'lang. Narxlarni /dxfind da tekshiring!")
    if ok == 0:   # paket o'lchamlari mos kelmadi (masalan Donatix 100, bizda 110): Donatix ro'yxatini ko'rsatamiz
        await m.answer("ℹ️ Donatix'dagi paketlar (bizniki bilan o'lchami farq qilishi mumkin):", parse_mode="HTML")
        await say_chunks(m, [pline(p) for p in prods[:30]])

@dp.message(Command("dxsync"))
async def dx_sync_cmd(m: Message, command: CommandObject):
    if m.from_user.id != C.ADMIN_ID or not DX.enabled(): return
    await m.answer("🔄 Donatix'dan olinyapti...")
    rep = await dx_sync((command.args or "").strip() or None)
    lines = []
    for gid, v in rep.items():
        if isinstance(v, tuple):
            n, regs, r, src = v
            lines.append(f"✅ <b>{H.escape(gid)}</b>: {n} ta" + (f" ({', '.join(regs)}) · region manbasi: {src}" if regs else " · ⚠ region topilmadi, /dxraw products?kind=topup&limit=2 natijasini yuboring") + f"\n    namuna: {H.escape(str(r[4]))} → ${r[7]} → <b>{dx_price_tjs(r[7])}</b> somoni")
        else: lines.append(f"❌ <b>{H.escape(gid)}</b>: {H.escape(str(v))}")
    await say_chunks(m, lines + ["", f"Ustama: +{C.DX_MARKUP * 100:g}% · kurs: {C.USD_TJS:g}", "Topilmaganlar uchun: /dxcats so'z va /dxcat o'yin_id kategoriya"])

@dp.message(Command("dxcat"))
async def dx_cat_set(m: Message, command: CommandObject):
    if m.from_user.id != C.ADMIN_ID: return
    a = (command.args or "").split()
    if len(a) != 2 or not any(x["id"] == a[0] for x in C.DX_GAMES):
        return await m.answer("Ishlatish: /dxcat o'yin_id kategoriya_id\nO'yinlar: " + ", ".join(x["id"] for x in C.DX_GAMES))
    D.dxgame_set(a[0], a[1], a[1]); await m.answer(f"✅ {a[0]} → {a[1]}. Endi /dxsync {a[0]} yozing.")

@dp.message(Command("dxraw"))
async def dx_raw(m: Message, command: CommandObject):
    if m.from_user.id != C.ADMIN_ID or not DX.enabled(): return
    p = (command.args or "").strip().lstrip("/")
    if not p or ".." in p: return await m.answer("Ishlatish: /dxraw glory/regions")
    st, d = await DX.call("GET", "/" + p)
    await m.answer(H.escape(f"HTTP {st}\n" + json.dumps(d, ensure_ascii=False)[:3500]), parse_mode="HTML")

async def on_error(event):
    logging.exception("bot error: %s", getattr(event, "exception", event)); return True
try: dp.error()(on_error)
except Exception: logging.warning("error handler not registered")

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

hits = {}; whits = {}
def _rl(store, k, lim):
    now = time.time(); store[k] = [x for x in store.get(k, []) if now - x < 60] + [now]
    return len(store[k]) > lim
@web.middleware
async def mw(req, handler):
    try:
        if req.method == "OPTIONS": r = web.Response()
        else:
            if req.path.startswith("/api/") and req.path != "/api/catalog":
                u = check_init(req.headers.get("X-Init", ""))
                if not u: return web.json_response({"error": "auth"}, status=401, headers=cors())
                req["u"] = D.user(u["id"], u.get("first_name", "")); req["tg"] = u
                # so'rovlar cheklovi: umumiy 60/daq, buyurtma/to'lov 12/daq
                if _rl(hits, u["id"], 60) or (req.method == "POST" and _rl(whits, u["id"], 12)):
                    return web.json_response({"error": "rate"}, status=429, headers=cors())
            r = await handler(req)
    except web.HTTPException: raise
    except Exception:
        logging.exception("api error: %s", req.path)
        return web.json_response({"error": "server"}, status=500, headers=cors())
    r.headers.update(cors()); return r
def cors():
    if not C.ORIGIN or C.ORIGIN == "*": return {}   # Mini App shu serverning o'zida, CORS kerak emas
    return {"Access-Control-Allow-Origin": C.ORIGIN, "Access-Control-Allow-Headers": "Content-Type,X-Init", "Access-Control-Allow-Methods": "GET,POST,OPTIONS"}
async def _sec(req, resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"; resp.headers["Referrer-Policy"] = "no-referrer"

async def catalog(r): return web.json_response({**C.CATALOG, "games": dx_catalog(), "bot": (await bot.me()).username, "support": C.SUPPORT, "rate": C.RATE, "pay": [{k: x[k] for k in ("id", "name", "type", "cur", "color", "icon")} for x in C.PAY]})
async def me(r):
    u = r["u"]; n = D.q("SELECT COUNT(*) c FROM users WHERE invited_by=?", (u["id"],)).fetchone()["c"]
    b = D.q("SELECT COUNT(*) c FROM users WHERE invited_by=? AND paid=1", (u["id"],)).fetchone()["c"]
    return web.json_response({"balance": round(u["balance"], 2), "spent": round(u["spent"], 2), "lang": u["lang"], "ref": u["ref"], "refs": n, "buyers": b, "bonus": round(u["bonus"], 2), "rating": rstats()})
async def lang(r):
    l = (await r.json()).get("lang")
    if l in ("ru", "uz", "tg", "en"): D.q("UPDATE users SET lang=?, lang_set=1 WHERE id=?", (l, r["u"]["id"]))
    return web.json_response({"ok": True})
CHK = {}; chk_hits = {}
def _jpath(d, p):
    for k in p.split("."):
        d = d[int(k)] if isinstance(d, list) else d.get(k)
        if d is None: return None
    return d
def _fetch(url, headers):
    req = urllib.request.Request(url, headers={"User-Agent": "diavex-bot", "Accept": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=6) as r: return r.status, r.read(200_000).decode("utf-8", "replace")
async def check_id(game, pid, region=""):
    """('ok', nik) = topildi | ('noid', '') = bunday ID yo'q | ('unv', '') = tekshirib bo'lmadi (API yo'q yoki xato)."""
    if DX.enabled() and DXSTATE["on"]:
        gg = next((x for x in C.CATALOG["games"] if x["id"] == game), None)
        sku = (dx_sku_any(gg, region) or await dx_discover(gg, region)) if gg else None
        if sku:
            key = (game, pid, region); now = time.time(); c = CHK.get(key)
            if c and now - c[0] < 600: return c[1], c[2]
            res = await DX.account_check(sku, pid)
            if res[0] != "unv":
                if len(CHK) > 2000: CHK.clear()
                CHK[key] = (now, *res)
            return res
    if not C.IDCHECK_URL: return "unv", ""
    key = (game, pid, region); now = time.time(); c = CHK.get(key)
    if c and now - c[0] < 600: return c[1], c[2]
    q = urllib.parse.quote
    url = C.IDCHECK_URL.replace("{game}", q(str(C.IDCHECK_GAMES.get(game, game)))).replace("{id}", q(pid)).replace("{region}", q(region or ""))
    try:
        st, body = await asyncio.to_thread(_fetch, url, C.IDCHECK_HEADERS)
        nick = _jpath(_json.loads(body), C.IDCHECK_NICK)
        res = ("ok", str(nick)[:40]) if nick else ("unv", "")
    except urllib.error.HTTPError as e:
        res = ("noid", "") if e.code == 404 else ("unv", "")
    except Exception:
        logging.exception("idcheck failed"); res = ("unv", "")
    if res[0] != "unv":
        if len(CHK) > 2000: CHK.clear()
        CHK[key] = (now, *res)
    return res
async def checkid(r):
    q = r.query; gid = q.get("game"); region = str(q.get("region") or "")
    try: raw = json.loads(q.get("fields") or "null")
    except Exception: raw = None
    if raw is None and q.get("id"): raw = {"player_id": q.get("id")}
    if _rl(chk_hits, r["u"]["id"], 10): return web.json_response({"error": "rate"}, status=429)
    gm = next((x for x in C.DX_GAMES if x["id"] == gid), None)
    if gm and D.dxcat_items(gid):   # Donatix'dan olingan o'yin
        row = D.dxcat_any(gid, region)
        if not row: return web.json_response({"error": "bad"})
        if gm["kind"].startswith("telegram"): return web.json_response({"ok": True, "nick": None})
        keys = [f.get("key") for f in json.loads(row["fields"] or "[]") if f.get("key")] or ["player_id"]
        fields = parse_fields(raw, keys)
        if not fields: return web.json_response({"error": "bad"})
        st, nick = await dx_check_fields(gid, row["product_id"], fields)
        if st == "noid": return web.json_response({"error": "noid"})
        return web.json_response({"ok": True, "nick": nick or None})
    g = next((x for x in C.CATALOG["games"] if x["id"] == gid), None)
    pid = str((raw or {}).get("player_id", "")).strip()
    if not g or not (pid.isdigit() and 5 <= len(pid) <= 14): return web.json_response({"error": "bad"})
    region = region if g.get("regions") and region in g["regions"] else ""
    st, nick = await check_id(g["id"], pid, region)
    if st == "noid": return web.json_response({"error": "noid"})
    return web.json_response({"ok": True, "nick": nick or None})

def now_s(): return datetime.now(timezone(timedelta(hours=C.TZ_HOURS))).strftime("%d.%m.%Y %H:%M")
def to_local(ts):
    try: return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=C.TZ_HOURS))).strftime("%d.%m.%Y %H:%M")
    except Exception: return str(ts or "—")
def order_caption(oid, game, product, pid, price, uid, full, un, when, nick=""):
    e = H.escape
    return (f"🛒 <b>Buyurtma #{oid}</b>\n🎮 O'yin: <b>{e(game)}</b>\n📦 Mahsulot: <b>{e(product)}</b>\n🆔 O'yinchi ID: <code>{e(str(pid))}</code>\n🎭 Nik: {("<b>" + e(nick) + "</b>") if nick else "⚠ tasdiqlanmagan"}\n💰 Summa: <b>{price:g} somoni</b>\n"
            f"👤 Ism: {e(full)}\n🔗 Username: {e(un)}\n🆔 Telegram ID: <code>{uid}</code>\n🕒 Vaqt: {when}")
def order_kb(oid):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Bajarildi", callback_data=f"od{oid}"), InlineKeyboardButton(text="❌ Rad etish", callback_data=f"or{oid}")]])
DXSTATE = {"on": True}; DX_RETRY = (5, 15); TASKS = set(); DX_WARNED = set()
TEMP_CODES = {"rate_limited", "not_available", "temporarily_unavailable", "supplier_unavailable"}
def dx_resolve(item_id, region):
    """Mahsulot Donatix'ga bog'langan va avto yoqilgan bo'lsa product_id, aks holda None (qo'lda)."""
    if not (DX.enabled() and DXSTATE["on"]): return None
    return D.dx_get(item_id, region or "") or D.dx_get(item_id, "")
def dx_sku_any(g, region):
    for items in g["tabs"].values():
        for it in items:
            s = D.dx_get(it["id"], region or "") or D.dx_get(it["id"], "")
            if s: return s
    return None
DISC = {}
async def dx_discover(g, region):
    """Bog'lash qilinmagan bo'lsa ham ID tekshirish ishlashi uchun: Donatix'dan shu o'yin (va region) uchun bitta mahsulotni o'zi topadi."""
    if not (DX.enabled() and DXSTATE["on"]): return None
    key = (g["id"], region or ""); c = DISC.get(key)
    if c and time.time() - c[0] < (3600 if c[1] else 300): return c[1]
    prods = [p for p in await DX.products(q=C.DX_QUERIES.get(g["id"], g["name"]), pages=1, limit=100) if p.get("product_id")]
    nz = lambda s: re.sub(r"[^a-z0-9]", "", str(s or "").lower())
    keys = [k for k in (nz(g["name"]), nz(C.DX_CATEGORIES.get(g["id"], ""))) if k]
    qk = nz(C.DX_QUERIES.get(g["id"], ""))
    # faqat shu o'yinga tegishli mahsulotlar (boshqa o'yinniki bilan adashmaslik uchun)
    mine = [p for p in prods if any(nz(p.get("category_id")).startswith(k) for k in keys) or (qk and nz(p.get("category_name")) == qk)]
    rg = (region or "").upper()
    pick = (next((p for p in mine if str(p.get("region") or "").upper() == rg and rg), None)
            or next((p for p in mine if str(p.get("region") or "").upper() in ("", "GLOBAL")), None)
            or (mine[0] if mine else None))
    sku = pick["product_id"] if pick else None
    DISC[key] = (time.time(), sku)
    return sku
async def admin_say(text, kb=None):
    try: await bot.send_message(C.ADMIN_ID, text, parse_mode="HTML", reply_markup=kb)
    except Exception: logging.exception("admin_say failed")
def order_row_caption(oid):
    o = D.q("SELECT o.*, u.name uname FROM orders o JOIN users u ON u.id=o.uid WHERE o.id=?", (oid,)).fetchone()
    if not o: return None, None
    prod = (o["title"] or "")[len(o["game"] or ""):].strip() or (o["item"] or "")
    return o, order_caption(o["id"], o["game"] or "", prod, o["pid"], o["price"], o["uid"], o["uname"] or "—", "—", to_local(o["ts"]), o["nick"] or "")
async def dx_manual(oid, reason):
    """Avto bo'lmadi: buyurtma 'pending' qoladi, admin qo'lda bajaradi yoki rad etadi."""
    o, cap = order_row_caption(oid)
    if o and o["status"] == "pending":
        await admin_say(cap + f"\n\n⚠ <b>Avto yuborilmadi:</b> {H.escape(str(reason))}\n👉 Qo'lda bajaring yoki rad eting.", order_kb(oid))
async def dx_done(oid):
    if D.order_finish(oid):
        o = D.q("SELECT * FROM orders WHERE id=?", (oid,)).fetchone()
        await notify(o["uid"], "done", o)
        await admin_say(f"✅ Buyurtma #{oid} Donatix orqali avto bajarildi.")
async def dx_fail(oid, why):
    o = D.cancel_order(oid)   # pul mijozga qaytadi
    if o:
        await tell(o["uid"], "ordrej", no=oid, amt=f"{o['price']:.2f}")
        await admin_say(f"❌ Buyurtma #{oid} bajarilmadi: {H.escape(str(why))}\n💰 Pul mijozga qaytarildi.")
def dx_price_tjs(usd, qty=1):
    """Donatix narxi (USD) -> bizning narx (somoni): kurs va ustama (standart +30%) bilan, 0.1 ga yuqoriga yaxlitlanadi."""
    return max(0.1, math.ceil(float(usd) * qty * C.USD_TJS * (1 + C.DX_MARKUP) * 10 - 1e-9) / 10)
nz = lambda s: re.sub(r"[^a-z0-9]", "", str(s or "").lower())
def _qty(name):
    mm = re.search(r"\d+", str(name or "")); return int(mm.group()) if mm else 0
def dx_match(p, gm, cat, qq):
    keys = [k for k in (nz(cat), nz(gm["name"])) if k]
    return any(nz(p.get("category_id")).startswith(k) for k in keys) or bool(nz(qq) and nz(p.get("category_name")) == nz(qq))
REGION_KEYS = ("region", "region_code", "region_id", "region_name", "region_title", "country", "country_code", "server", "zone", "locale", "area")
def p_region(p):
    for k in REGION_KEYS:
        v = p.get(k)
        if v not in (None, "", []): return str(v)
    return ""
def tab_for(name, emo, kind):
    if kind == "telegram_stars": return "⭐"
    if kind.startswith("telegram"): return "💎"
    mm = re.match(r"\s*\d[\d\s.,]*\s*(.*)", str(name))
    if mm and re.match(r"\s*\d", str(name)):   # raqam bilan boshlansa: valyuta paketi (Diamonds, UC, ...)
        unit = re.sub(r"[^\w\s+.\-]", "", mm.group(1), flags=re.UNICODE).strip()[:14]
        return f"{emo or '💎'} {unit}".strip()
    return "📑 Pass"
async def dx_sync(only=None):
    """Donatix'dan o'yinlar va paketlarni oladi (miqdorlari Donatix'dagidek, region bo'yicha). {o'yin_id: (soni, regionlar, namuna, manba) | xato matni}"""
    rep = {}
    if not C.USD_TJS: return {"_": "USD_TJS yozilmagan (Render → Environment)"}
    for gm in C.DX_GAMES:
        if only and gm["id"] != only: continue
        cfg = D.dxgame_get(gm["id"]); cat = (cfg["cat"] if cfg else "") or gm.get("cat", ""); qq = (cfg["q"] if cfg else "") or gm.get("q", "")
        kind = gm["kind"]; tg = kind.startswith("telegram"); found_all = None
        try:
            if tg: prods = [p for p in await DX.products(kind=kind, pages=1, limit=100) if str(p.get("kind") or kind) == kind]
            else:
                prods = await DX.products(category=cat) if cat else []
                if not prods and qq:
                    found_all = await DX.products(q=qq)
                    prods = [p for p in found_all if dx_match(p, gm, cat, qq)]
            prods = [p for p in prods if p.get("product_id")]
            if not prods:
                hint = ""
                if found_all:
                    cats = {}
                    for p in found_all: cats.setdefault(str(p.get("category_id")), str(p.get("category_name") or ""))
                    hint = ". Qidiruvda topilgan kategoriyalar: " + ", ".join(f"{k} ({v})" for k, v in list(cats.items())[:8]) + f" → /dxcat {gm['id']} kategoriya_id"
                rep[gm["id"]] = "Donatix'da mahsulot topilmadi" + hint; continue
            regs = [p_region(p) for p in prods]; src = "region" if any(regs) else ""
            if not any(regs):   # region maydoni yo'q: kategoriya nomidagi qo'shimchadan olamiz (free_fire_cis -> CIS)
                cats = [str(p.get("category_id") or "") for p in prods]
                if len(set(cats)) > 1:
                    pre = os.path.commonprefix(cats)
                    regs = [(c[len(pre):].strip("_- ") or str(p.get("category_name") or "")).upper() for c, p in zip(cats, prods)]; src = "kategoriya"
            if not any(regs):   # nom oxiridagi (CIS) / [Global]
                nm = [re.search(r"[\(\[]([^\)\]]{2,20})[\)\]]\s*$", str(p.get("name") or "")) for p in prods]
                if sum(1 for x in nm if x) * 2 >= len(prods) and any(nm): regs = [x.group(1).upper() if x else "" for x in nm]; src = "nom"
            best = {}
            for p, rg in zip(prods, regs):
                try: usd = float(p.get("price_usd") or 0)
                except Exception: usd = 0
                if usd <= 0: continue
                name = str(p.get("name") or p.get("title") or p["product_id"]); emo = p.get("emoji") or ""
                shown = name if (not emo or emo in name) else f"{name} {emo}"
                title = str(p.get("region_title") or rg)
                row = (p["product_id"], gm["id"], rg, title, shown, tab_for(name, emo, kind), emo, usd,
                       json.dumps(p.get("fields") or [], ensure_ascii=False), kind, _qty(name), int(p.get("min_quantity") or 0), int(p.get("max_quantity") or 0))
                k = (rg, shown)
                if k not in best or usd < best[k][7]: best[k] = row   # bir xil paket takrorlansa eng arzonini qoldiramiz
            rows = list(best.values())
            if not rows: rep[gm["id"]] = "Donatix'da mahsulot topilmadi"; continue
            D.dxcat_replace(gm["id"], rows)
            rep[gm["id"]] = (len(rows), sorted({r[2] for r in rows if r[2]}), rows[0], src or "yo'q")
        except Exception as e:
            logging.exception("dx_sync"); rep[gm["id"]] = f"xato: {e}"
    return rep
def dx_catalog():
    """Mini App uchun o'yinlar: Donatix'dan sinxronlanganlar (bo'lsa), qolganlari catalog.json dan."""
    dyn = {}
    for gm in C.DX_GAMES:
        rows = D.dxcat_items(gm["id"])
        if not rows or not C.USD_TJS: continue
        kind = gm["kind"]; tg = kind.startswith("telegram")
        try: fl = json.loads(rows[0]["fields"] or "[]")
        except Exception: fl = []
        if not fl: fl = [{"key": "telegram_username" if tg else "player_id"}]
        g = {"id": gm["id"], "name": gm["name"], "sub": gm.get("sub", ""), "icon": gm.get("icon", "🎮"), "color": gm.get("color", "#334"), "kind": kind,
             "fields": [{"key": f.get("key"), "label": f.get("label") or ""} for f in fl if f.get("key") and re.fullmatch(r"\w+", str(f.get("key")))], "nocheck": tg, "tabs": {}}
        if kind == "telegram_stars":
            r = rows[0]; lo, hi = r["qmin"] or 50, r["qmax"] or 10000
            g["stars"] = {"id": r["product_id"], "unit": r["price_usd"] * C.USD_TJS * (1 + C.DX_MARKUP), "min": lo, "max": hi, "presets": [p for p in (50, 100, 250, 500, 1000, 2500, 5000) if lo <= p <= hi] or [lo]}
            g["tabs"] = {"⭐": []}
        else:
            regs = []
            for r in rows:
                if r["region"] and r["region"] not in regs: regs.append(r["region"])
                g["tabs"].setdefault(r["tab"], []).append({"id": r["product_id"], "name": r["name"], "price": dx_price_tjs(r["price_usd"]), "region": r["region"]})
            regs.sort(key=lambda x: (0 if x.upper() == "CIS" else 1 if x.upper() == "GLOBAL" else 2, x))
            if regs: g["regions"] = regs; g["region_titles"] = {r["region"]: r["region_title"] for r in rows if r["region"]}
        dyn[gm["id"]] = g
    return [dyn[x["id"]] for x in C.DX_GAMES if x["id"] in dyn] + [x for x in C.CATALOG["games"] if x["id"] not in dyn]
def dx_find(gid, iid):
    gm = next((x for x in C.DX_GAMES if x["id"] == gid), None); r = D.dxcat_get(str(iid or ""))
    return (gm, r) if gm and r and r["game_id"] == gid and C.USD_TJS else None
def parse_fields(raw, keys):
    """Mijoz yuborgan maydonlarni tekshiradi (faqat ruxsat etilgan kalitlar, qisqa matn)."""
    if not isinstance(raw, dict): return None
    out = {}
    for k in keys:
        v = str(raw.get(k, "")).strip()
        if k == "telegram_username":
            v = v.lstrip("@")
            if not re.fullmatch(r"[A-Za-z0-9_]{5,32}", v): return None
            v = "@" + v
        elif not re.fullmatch(r"[#@\w.\-]{1,40}", v): return None
        out[k] = v
    return out
async def dx_check_fields(gid, sku, fields):
    key = (gid, sku, json.dumps(fields, sort_keys=True)); now = time.time(); c = CHK.get(key)
    if c and now - c[0] < 600: return c[1], c[2]
    res = await DX.account_check(sku, fields)
    if res[0] != "unv":
        if len(CHK) > 2000: CHK.clear()
        CHK[key] = (now, *res)
    return res
async def dx_place(oid, price, sku, fields, qty=None):
    try:
        prod = await DX.product(sku)
        if not prod: return await dx_manual(oid, "Donatix mahsuloti topilmadi")
        missing = [str(f.get("key")) for f in (prod.get("fields") or []) if f.get("key") not in fields]
        if missing: return await dx_manual(oid, "qo'shimcha maydon kerak: " + ", ".join(missing))
        if C.USD_TJS:
            try: cost = float(prod.get("price_usd")) * (qty or 1) * C.USD_TJS
            except Exception: cost = None
            if cost is not None and cost > price:
                return await dx_manual(oid, f"tannarx {cost:.2f} somoni sotuv narxidan ({price:g}) yuqori")
        key = f"diavex-{oid}"   # bir xil kalit: qayta urinishda pul ikki marta yechilmaydi
        for n in range(len(DX_RETRY) + 1):
            st, d = await DX.create_order(sku, fields, key, qty); code = DX.err_code(d)
            if st in (200, 201) and d and d.get("ok"):
                od = d.get("order") or {}
                if od.get("order_id") and D.dx_attach(oid, str(od["order_id"])):
                    if od.get("status") == "completed": await dx_done(oid)
                    elif od.get("status") == "failed": await dx_fail(oid, od.get("error") or "Donatix: failed")
                    return
                return await dx_manual(oid, "Donatix javobi tushunarsiz, panelni tekshiring")
            if st == 400 and code in ("player_not_found", "account_not_found"):
                return await dx_fail(oid, "bunday o'yinchi ID topilmadi")
            if not (st in (0, 429, 503) or code in TEMP_CODES):
                return await dx_manual(oid, f"{st} {code or (d or {}).get('error', '')}"[:200])
            if n < len(DX_RETRY): await asyncio.sleep(DX_RETRY[n])
        await dx_manual(oid, "Donatix javob bermadi. Buyurtma u yerda yaratilgan bo'lishi mumkin, avval Donatix panelida tekshiring (donat ikki marta yuborilmasin)")
    except Exception:
        logging.exception("dx_place failed"); await dx_manual(oid, "ichki xato (Render Logs'ni tekshiring)")
async def dx_poll_once():
    rows = D.q("SELECT id, dx_id, ts FROM orders WHERE status='processing' AND dx_id!='' ORDER BY id LIMIT 40").fetchall()
    for o in rows:
        st, d = await DX.order_status(o["dx_id"])
        if st == 200 and d and d.get("ok"):
            od = d.get("order") or {}; s = od.get("status")
            if s == "completed": await dx_done(o["id"]); continue
            if s == "failed": await dx_fail(o["id"], od.get("error") or "Donatix: failed"); continue
        try: age = (datetime.now(timezone.utc) - datetime.strptime(o["ts"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)).total_seconds()
        except Exception: age = 0
        if age > 1800 and o["id"] not in DX_WARNED:
            DX_WARNED.add(o["id"]); await admin_say(f"⏰ Buyurtma #{o['id']} 30 daqiqadan beri Donatix'da bajarilmayapti (<code>{H.escape(str(o['dx_id']))}</code>). Panelda tekshiring.")
async def dx_worker():
    last_bal = 0; warned = 0; last_sync = time.time()
    while True:
        try:
            if DX.enabled():
                await dx_poll_once()
                if time.time() - last_sync > 1800:   # katalog va narxlar har 30 daqiqada yangilanadi
                    last_sync = time.time()
                    for gid in D.dxcat_game_ids(): await dx_sync(gid)
                if time.time() - last_bal > 600:
                    last_bal = time.time(); b = await DX.balance()
                    if b is not None and b < C.DX_MIN_BALANCE and time.time() - warned > 6 * 3600:
                        warned = time.time(); await admin_say(f"⚠ Donatix balansi kam: ${b:.2f}. To'ldiring, aks holda buyurtmalar qo'lda keladi.")
        except Exception: logging.exception("dx_worker")
        await asyncio.sleep(8)
async def order(r):
    d = await r.json(); uid = r["u"]["id"]; tg = r["tg"]
    dyn = dx_find(d.get("game"), d.get("item"))
    if dyn:   # Donatix'dan olingan mahsulot: narx Donatix narxi + ustama
        gm, row = dyn; kind = row["kind"]; stars = kind == "telegram_stars"
        try: fl = [f.get("key") for f in json.loads(row["fields"] or "[]") if f.get("key")]
        except Exception: fl = []
        fields = parse_fields(d.get("fields"), fl or ["telegram_username" if kind.startswith("telegram") else "player_id"])
        if not fields: return web.json_response({"error": "bad"})
        qty = 1
        if stars:
            try: qty = int(d.get("qty"))
            except Exception: return web.json_response({"error": "bad"})
            if not (row["qmin"] <= qty <= row["qmax"]): return web.json_response({"error": "bad"})
        price = dx_price_tjs(row["price_usd"], qty); region = row["region"] or ""
        gname = gm["name"]; iname = row["name"] + (f" × {qty}" if stars else "")
        product = iname + (f" [{region}]" if region else ""); pid = " / ".join(fields.values()); nick = ""
        if not kind.startswith("telegram"):
            st, nick = await dx_check_fields(gm["id"], row["product_id"], fields)
            if st == "noid": return web.json_response({"error": "noid"})
        sku = row["product_id"] if (DX.enabled() and DXSTATE["on"]) else None
        fj = json.dumps(fields, ensure_ascii=False)
    else:   # catalog.json dagi (qo'lda) mahsulot
        g, i = C.find_item(d.get("game"), d.get("item"))
        pid = str(d.get("pid", "")).strip()
        if not i or not (pid.isdigit() and 5 <= len(pid) <= 14): return web.json_response({"error": "bad"})
        region = ""
        if g.get("regions"): region = d.get("region") if d.get("region") in g["regions"] else g["regions"][0]
        gname = g["name"]; iname = i["name"]; price = i["price"]; qty = 1; stars = False; fj = ""
        product = iname + (f" [{region}]" if region else "")
        st, nick = await check_id(g["id"], pid, region)   # ID ni server o'zi tekshiradi
        if st == "noid": return web.json_response({"error": "noid"})
        sku = dx_resolve(i["id"], region); fields = {"player_id": pid}   # Donatix'ga bog'langan bo'lsa avto
    oid = D.buy(uid, f"{gname} {product}", pid, price, gname, iname, fj, qty)  # narx serverdan olinadi
    if oid == -1: return web.json_response({"error": "pending"})
    if not oid: return web.json_response({"error": "funds", "need": price, "balance": round(D.user(uid)["balance"], 2)})
    if nick: D.q("UPDATE orders SET nick=? WHERE id=?", (nick, oid))
    full = f"{tg.get('first_name', '')} {tg.get('last_name', '')}".strip() or "—"
    un = f"@{tg['username']}" if tg.get("username") else "—"
    try:
        cap = order_caption(oid, gname, product, pid, price, uid, full, un, now_s(), nick)
        if sku: await bot.send_message(C.ADMIN_ID, cap + "\n\n🤖 <i>Donatix orqali avto yuborilmoqda...</i>", parse_mode="HTML")
        else: await bot.send_message(C.ADMIN_ID, cap, parse_mode="HTML", reply_markup=order_kb(oid))
    except Exception:
        logging.exception("order: admin send failed"); D.cancel_order(oid)   # pul qaytariladi
        return web.json_response({"error": "send"})
    await notify(uid, "acc", D.q("SELECT * FROM orders WHERE id=?", (oid,)).fetchone())
    if sku:
        t = asyncio.create_task(dx_place(oid, price, sku, fields, qty if stars else None)); TASKS.add(t); t.add_done_callback(TASKS.discard)
    return web.json_response({"ok": True, "balance": round(D.user(uid)["balance"], 2), "price": price, "game": gname, "item": iname, "nick": nick})

async def topup(r):
    d = await r.json()
    try: a = float(d.get("amount", 0))
    except Exception: a = 0
    x = next((p for p in C.PAY if p["id"] == d.get("method")), None)
    if not x or not 10 <= a <= 5000: return web.json_response({"error": "bad"})
    if D.has_pending(r["u"]["id"]): return web.json_response({"error": "pending"})
    pa = a if x["cur"] == "TJS" else round(a / C.RATE)
    return web.json_response({"ok": True, "id": 0, "amount": a, "pay": pa, "cur": x["cur"], "type": x["type"], "value": x["value"], "holder": x["holder"], "name": x["name"], "icon": x["icon"], "color": x["color"], "method": x["id"]})
def _digits(s): return re.sub(r"\D", "", str(s or ""))
def ai_report(res, want, value):
    """AI natijasini admin uchun matnga aylantiradi (qaror admin'da qoladi)."""
    if not res: return "🤖 AI tekshiruv: natija olinmadi"
    e = H.escape; L = []; warn = False
    if res.get("is_receipt") is False: L.append("🚨 Bu o'tkazma cheki emasga o'xshaydi"); warn = True
    if res.get("status") == "failed": L.append("⚠ O'tkazma muvaffaqiyatsiz ko'rinadi"); warn = True
    amt = res.get("amount")
    if isinstance(amt, (int, float)):
        if abs(float(amt) - want) > 0.01: L.append(f"⚠ Summa mos emas: chekda {amt:g}, so'ralgan {want:g}"); warn = True
    elif res.get("is_receipt") is not False: L.append("⚠ Summa chekdan o'qilmadi"); warn = True
    rcp, mine = _digits(res.get("recipient")), _digits(value)
    if mine and rcp and mine[-4:] not in rcp: L.append("⚠ Qabul qiluvchi raqam bizniki bilan mos emas"); warn = True
    try:
        dt = datetime.strptime(str(res.get("date")), "%Y-%m-%d %H:%M"); now = datetime.now(timezone(timedelta(hours=C.TZ_HOURS))).replace(tzinfo=None)
        if dt > now + timedelta(hours=1): L.append("⚠ Chek sanasi kelajakda"); warn = True
        elif dt < now - timedelta(hours=36): L.append("⚠ Chek eski (36 soatdan ortiq)"); warn = True
    except Exception: pass
    ts = [str(x) for x in (res.get("tamper_signs") or [])][:3]
    if ts: L.append("⚠ Tahrir belgilari: " + e(", ".join(ts))); warn = True
    info = []
    if isinstance(amt, (int, float)): info.append(f"summa {amt:g} {e(str(res.get('currency') or ''))}".strip())
    if res.get("date"): info.append("sana " + e(str(res["date"])))
    if res.get("recipient"): info.append("qabul qiluvchi " + e(str(res["recipient"])))
    return ("🤖 <b>AI tekshiruv:</b> " + ("⚠ <b>shubhali</b>" if warn else "✅ <b>mos keladi</b>")) + ("\n" + "\n".join(L) if L else "") + ("\n<i>Chekda: " + "; ".join(info) + "</i>" if info else "")
async def rcpt_ai_task(tid, msg_id, cap, kb, raw, want, value):
    try:
        txt = ai_report(await AI.analyze(raw, "image/png" if raw[:4] == b"\x89PNG" else "image/jpeg"), want, value)
        t = D.q("SELECT status FROM topups WHERE id=?", (tid,)).fetchone()
        await bot.edit_message_caption(chat_id=C.ADMIN_ID, message_id=msg_id, caption=cap + "\n\n" + txt, parse_mode="HTML", reply_markup=kb if (t and t["status"] == "pending") else None)
    except Exception: logging.exception("rcpt_ai_task")
async def receipt_api(r):
    d = await r.json(); uid = r["u"]["id"]; tg = r["tg"]
    try: a = float(d.get("amount", 0))
    except Exception: a = 0
    x = next((p for p in C.PAY if p["id"] == d.get("method")), None)
    try: raw = base64.b64decode(str(d.get("image", "")).split(",")[-1], validate=True)
    except Exception: raw = b""
    if not x or not 10 <= a <= 5000 or not 1000 < len(raw) < 6_000_000 or not (raw[:3] == b"\xff\xd8\xff" or raw[:4] == b"\x89PNG"):
        return web.json_response({"error": "bad"})
    h = hashlib.sha256(raw).hexdigest()
    if D.rhash_get(h): return web.json_response({"error": "dup"})   # shu chek avval ishlatilgan
    tid = D.add_topup(uid, a, x["id"])
    if tid == -1: return web.json_response({"error": "pending"})
    e = H.escape
    when = datetime.now(timezone(timedelta(hours=C.TZ_HOURS))).strftime("%d.%m.%Y %H:%M")
    full = f"{tg.get('first_name', '')} {tg.get('last_name', '')}".strip() or "—"
    un = f"@{tg['username']}" if tg.get("username") else "—"
    cap = (f"💳 <b>Balans to'ldirish #{tid}</b>\n🏦 Usul: <b>{e(x['name'].upper())}</b>\n💵 Mablag': <b>{a:g} somoni</b>\n"
           f"🆔 Telegram ID: <code>{uid}</code>\n👤 Ism: {e(full)}\n🔗 Username: {e(un)}\n🕒 Vaqt: {when}")
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"ok{tid}"), InlineKeyboardButton(text="❌ Rad etish", callback_data=f"no{tid}")]])
    if AI.enabled(): cap += "\n\n🤖 AI tekshirmoqda..."
    try: sent = await bot.send_photo(C.ADMIN_ID, BufferedInputFile(raw, "receipt.jpg"), caption=cap, parse_mode="HTML", reply_markup=kb)
    except Exception:
        logging.exception("receipt: admin send failed"); D.q("DELETE FROM topups WHERE id=?", (tid,))
        return web.json_response({"error": "send"})
    D.rhash_add(h, tid)
    if AI.enabled():
        tk = asyncio.create_task(rcpt_ai_task(tid, sent.message_id, cap.replace("\n\n🤖 AI tekshirmoqda...", ""), kb, raw, a, x["value"])); TASKS.add(tk); tk.add_done_callback(TASKS.discard)
    await tell(uid, "rcv", no=tid, amt=f"{a:g}", method=f"{x['name']} ({T[lang_of(uid)]['kind_' + x['type']]})")
    return web.json_response({"ok": True})
async def reviews(r):
    rows = D.q("SELECT r.oid, r.stars, r.text, r.reply, r.ts, o.game, o.item, o.title, u.name FROM ratings r JOIN orders o ON o.id=r.oid JOIN users u ON u.id=r.uid ORDER BY r.oid DESC LIMIT 300").fetchall()
    dt = lambda s: f"{s[8:10]}.{s[5:7]}.{s[:4]}" if s else ""
    items = [{"id": x["oid"], "name": (x["name"] or "?")[:20], "stars": x["stars"], "game": x["game"] or "", "item": x["item"] or x["title"], "text": x["text"] or "", "reply": x["reply"] or "", "date": dt(x["ts"])} for x in rows]
    return web.json_response({**rstats(), "items": items})
async def top_api(r):
    kind = r.query.get("kind", "donors"); cut = {"week": "-7 days", "month": "-30 days"}.get(r.query.get("period", "week"))
    a = (cut,) if cut else ()
    if kind == "topups":
        w = "AND f.ts >= datetime('now', ?)" if cut else ""
        rows = D.q(f"SELECT u.name, SUM(f.amount) s FROM fin f JOIN users u ON u.id=f.uid WHERE f.title='Top up' {w} GROUP BY f.uid ORDER BY s DESC LIMIT 20", a)
    else:
        w = "AND o.ts >= datetime('now', ?)" if cut else ""
        rows = D.q(f"SELECT u.name, SUM(o.price) s FROM orders o JOIN users u ON u.id=o.uid WHERE o.status!='cancelled' {w} GROUP BY o.uid ORDER BY s DESC LIMIT 20", a)
    return web.json_response({"items": [{"name": (x["name"] or "?")[:20], "total": round(x["s"] or 0, 2)} for x in rows]})
async def history(r):
    uid = r["u"]["id"]; f = lambda x: (lambda s: f"{s[8:10]}.{s[5:7]}.{s[:4]} {s[11:16]}" if len(s) >= 16 else s)(str(x or ""))
    o = [{"id": x["id"], "title": x["title"], "price": x["price"], "status": x["status"], "date": f(x["ts"]), "game": x["game"] or "", "item": x["item"] or ""} for x in D.q("SELECT * FROM orders WHERE uid=? ORDER BY id DESC LIMIT 50", (uid,))]
    n = [{"title": x["title"], "amount": x["amount"], "date": f(x["ts"])} for x in D.q("SELECT * FROM fin WHERE uid=? ORDER BY id DESC LIMIT 50", (uid,))]
    return web.json_response({"orders": o, "fin": n})

def _img(path):
    async def h(r):
        return web.FileResponse(path) if os.path.exists(path) else web.Response(status=404)
    return h
async def main():
    app = web.Application(middlewares=[mw], client_max_size=8 * 1024 * 1024)
    app.on_response_prepare.append(_sec)
    app.add_routes([web.get("/api/catalog", catalog), web.get("/api/me", me), web.post("/api/lang", lang), web.post("/api/order", order),
                    web.post("/api/topup", topup), web.post("/api/receipt", receipt_api), web.get("/api/history", history), web.get("/api/top", top_api), web.get("/api/checkid", checkid), web.get("/api/reviews", reviews), web.route("OPTIONS", "/{p:.*}", lambda r: web.Response()),
                    web.get("/", lambda r: web.FileResponse(os.path.join(HERE, "index.html")))])
    for f in ("style.css", "app.js", "i18n.js", "ru.json", "uz.json", "tg.json", "en.json", "logo.png", "splash.jpg"):
        app.router.add_get("/" + f, lambda r, f=f: web.FileResponse(os.path.join(HERE, f)))
    for g in C.CATALOG["games"]:
        app.router.add_get("/" + g["id"] + ".png", _img(os.path.join(HERE, g["id"] + ".png")))
    for x in C.PAY:
        app.router.add_get("/" + x["id"] + ".png", _img(os.path.join(HERE, x["id"] + ".png")))
    run = web.AppRunner(app); await run.setup(); await web.TCPSite(run, "0.0.0.0", C.PORT).start()
    _t = asyncio.create_task(dx_worker()); TASKS.add(_t)
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())
