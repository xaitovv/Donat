import html as H
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
import config as C, database as D

# Baza tuzilmasini o'zi tekshiradi (database.py eski bo'lsa ham ishlayveradi)
for _s in ("CREATE TABLE IF NOT EXISTS ratings(oid INTEGER PRIMARY KEY,uid INTEGER,stars INTEGER)",
           "ALTER TABLE users ADD COLUMN lang_set INTEGER DEFAULT 0",
           "ALTER TABLE orders ADD COLUMN game TEXT DEFAULT ''",
           "ALTER TABLE orders ADD COLUMN item TEXT DEFAULT ''",
           "ALTER TABLE ratings ADD COLUMN text TEXT DEFAULT ''",
           "ALTER TABLE ratings ADD COLUMN reply TEXT DEFAULT ''",
           "ALTER TABLE ratings ADD COLUMN ts TEXT",
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
    await m.answer(f"⏳ Kutilayotgan buyurtmalar: {len(rows)}\n⏳ Kutilayotgan to'lovlar: {n} (ularning cheki o'z xabarida, tugmalari bilan)")
    for o in rows:
        prod = (o["title"] or "")[len(o["game"] or ""):].strip() or (o["item"] or "")
        await m.answer(order_caption(o["id"], o["game"] or "", prod, o["pid"], o["price"], o["uid"], o["uname"] or "—", "—", to_local(o["ts"])), parse_mode="HTML", reply_markup=order_kb(o["id"]))

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

async def catalog(r): return web.json_response({**C.CATALOG, "bot": (await bot.me()).username, "support": C.SUPPORT, "rate": C.RATE, "pay": [{k: x[k] for k in ("id", "name", "type", "cur", "color", "icon")} for x in C.PAY]})
async def me(r):
    u = r["u"]; n = D.q("SELECT COUNT(*) c FROM users WHERE invited_by=?", (u["id"],)).fetchone()["c"]
    b = D.q("SELECT COUNT(*) c FROM users WHERE invited_by=? AND paid=1", (u["id"],)).fetchone()["c"]
    return web.json_response({"balance": round(u["balance"], 2), "spent": round(u["spent"], 2), "lang": u["lang"], "ref": u["ref"], "refs": n, "buyers": b, "bonus": round(u["bonus"], 2), "rating": rstats()})
async def lang(r):
    l = (await r.json()).get("lang")
    if l in ("ru", "uz", "tg", "en"): D.q("UPDATE users SET lang=?, lang_set=1 WHERE id=?", (l, r["u"]["id"]))
    return web.json_response({"ok": True})
def now_s(): return datetime.now(timezone(timedelta(hours=C.TZ_HOURS))).strftime("%d.%m.%Y %H:%M")
def to_local(ts):
    try: return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=C.TZ_HOURS))).strftime("%d.%m.%Y %H:%M")
    except Exception: return str(ts or "—")
def order_caption(oid, game, product, pid, price, uid, full, un, when):
    e = H.escape
    return (f"🛒 <b>Buyurtma #{oid}</b>\n🎮 O'yin: <b>{e(game)}</b>\n📦 Mahsulot: <b>{e(product)}</b>\n🆔 O'yinchi ID: <code>{e(str(pid))}</code>\n💰 Summa: <b>{price:g} somoni</b>\n"
            f"👤 Ism: {e(full)}\n🔗 Username: {e(un)}\n🆔 Telegram ID: <code>{uid}</code>\n🕒 Vaqt: {when}")
def order_kb(oid):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Bajarildi", callback_data=f"od{oid}"), InlineKeyboardButton(text="❌ Rad etish", callback_data=f"or{oid}")]])
async def order(r):
    d = await r.json(); uid = r["u"]["id"]; tg = r["tg"]
    g, i = C.find_item(d.get("game"), d.get("item"))
    pid = str(d.get("pid", "")).strip()
    if not i or not (pid.isdigit() and 5 <= len(pid) <= 14): return web.json_response({"error": "bad"})
    region = ""
    if g.get("regions"): region = d.get("region") if d.get("region") in g["regions"] else g["regions"][0]
    product = i["name"] + (f" [{region}]" if region else "")
    oid = D.buy(uid, f"{g['name']} {product}", pid, i["price"], g["name"], i["name"])  # narx serverdan olinadi
    if oid == -1: return web.json_response({"error": "pending"})
    if not oid: return web.json_response({"error": "funds"})
    full = f"{tg.get('first_name', '')} {tg.get('last_name', '')}".strip() or "—"
    un = f"@{tg['username']}" if tg.get("username") else "—"
    try:
        await bot.send_message(C.ADMIN_ID, order_caption(oid, g["name"], product, pid, i["price"], uid, full, un, now_s()), parse_mode="HTML", reply_markup=order_kb(oid))
    except Exception:
        logging.exception("order: admin send failed"); D.cancel_order(oid)   # pul qaytariladi
        return web.json_response({"error": "send"})
    await notify(uid, "acc", D.q("SELECT * FROM orders WHERE id=?", (oid,)).fetchone())
    return web.json_response({"ok": True, "balance": round(D.user(uid)["balance"], 2)})
async def topup(r):
    d = await r.json()
    try: a = float(d.get("amount", 0))
    except Exception: a = 0
    x = next((p for p in C.PAY if p["id"] == d.get("method")), None)
    if not x or not 10 <= a <= 5000: return web.json_response({"error": "bad"})
    if D.has_pending(r["u"]["id"]): return web.json_response({"error": "pending"})
    pa = a if x["cur"] == "TJS" else round(a / C.RATE)
    return web.json_response({"ok": True, "id": 0, "amount": a, "pay": pa, "cur": x["cur"], "type": x["type"], "value": x["value"], "holder": x["holder"], "name": x["name"], "icon": x["icon"], "color": x["color"], "method": x["id"]})
async def receipt_api(r):
    d = await r.json(); uid = r["u"]["id"]; tg = r["tg"]
    try: a = float(d.get("amount", 0))
    except Exception: a = 0
    x = next((p for p in C.PAY if p["id"] == d.get("method")), None)
    try: raw = base64.b64decode(str(d.get("image", "")).split(",")[-1], validate=True)
    except Exception: raw = b""
    if not x or not 10 <= a <= 5000 or not 1000 < len(raw) < 6_000_000 or not (raw[:3] == b"\xff\xd8\xff" or raw[:4] == b"\x89PNG"):
        return web.json_response({"error": "bad"})
    tid = D.add_topup(uid, a, x["id"])
    if tid == -1: return web.json_response({"error": "pending"})
    e = H.escape
    when = datetime.now(timezone(timedelta(hours=C.TZ_HOURS))).strftime("%d.%m.%Y %H:%M")
    full = f"{tg.get('first_name', '')} {tg.get('last_name', '')}".strip() or "—"
    un = f"@{tg['username']}" if tg.get("username") else "—"
    cap = (f"💳 <b>Balans to'ldirish #{tid}</b>\n🏦 Usul: <b>{e(x['name'].upper())}</b>\n💵 Mablag': <b>{a:g} somoni</b>\n"
           f"🆔 Telegram ID: <code>{uid}</code>\n👤 Ism: {e(full)}\n🔗 Username: {e(un)}\n🕒 Vaqt: {when}")
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"ok{tid}"), InlineKeyboardButton(text="❌ Rad etish", callback_data=f"no{tid}")]])
    try: await bot.send_photo(C.ADMIN_ID, BufferedInputFile(raw, "receipt.jpg"), caption=cap, parse_mode="HTML", reply_markup=kb)
    except Exception:
        logging.exception("receipt: admin send failed"); D.q("DELETE FROM topups WHERE id=?", (tid,))
        return web.json_response({"error": "send"})
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
                    web.post("/api/topup", topup), web.post("/api/receipt", receipt_api), web.get("/api/history", history), web.get("/api/top", top_api), web.get("/api/reviews", reviews), web.route("OPTIONS", "/{p:.*}", lambda r: web.Response()),
                    web.get("/", lambda r: web.FileResponse(os.path.join(HERE, "index.html")))])
    for f in ("style.css", "app.js", "i18n.js", "ru.json", "uz.json", "tg.json", "en.json", "logo.png", "splash.jpg"):
        app.router.add_get("/" + f, lambda r, f=f: web.FileResponse(os.path.join(HERE, f)))
    for g in C.CATALOG["games"]:
        app.router.add_get("/" + g["id"] + ".png", _img(os.path.join(HERE, g["id"] + ".png")))
    for x in C.PAY:
        app.router.add_get("/" + x["id"] + ".png", _img(os.path.join(HERE, x["id"] + ".png")))
    run = web.AppRunner(app); await run.setup(); await web.TCPSite(run, "0.0.0.0", C.PORT).start()
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())
