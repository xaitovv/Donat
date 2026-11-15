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
                           InlineKeyboardButton, WebAppInfo, BufferedInputFile, FSInputFile, InputMediaDocument)
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
           "CREATE TABLE IF NOT EXISTS settings(k TEXT PRIMARY KEY,v TEXT)",
           "CREATE TABLE IF NOT EXISTS catover(item_id TEXT PRIMARY KEY,name TEXT,price REAL,hidden INTEGER DEFAULT 0)",
           "CREATE TABLE IF NOT EXISTS catcust(id INTEGER PRIMARY KEY AUTOINCREMENT,game_id TEXT,region TEXT,tab TEXT,name TEXT,price REAL,sku TEXT DEFAULT '',hidden INTEGER DEFAULT 0)",
           "CREATE TABLE IF NOT EXISTS catregion(game_id TEXT,region TEXT,title TEXT,hidden INTEGER DEFAULT 0,PRIMARY KEY(game_id,region))",
           "CREATE TABLE IF NOT EXISTS gamehide(game_id TEXT PRIMARY KEY)",
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
    if C.ORDERS_URL.startswith("http"): r.append(InlineKeyboardButton(text=w["ord"], url=C.ORDERS_URL))
    elif ok: r.append(InlineKeyboardButton(text=w["ord"], web_app=WebAppInfo(url=url.rstrip("/") + "/?go=hist")))
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


# ---------- MAJBURIY OBUNA ----------
_TS = {
 "uz": dict(t="🔒 <b>Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling</b>\n\nObuna bo'lgach «✅ Tekshirish» tugmasini bosing.", chk="✅ Tekshirish", no="❌ Siz hali hamma kanalga obuna bo'lmagansiz!"),
 "tg": dict(t="🔒 <b>Барои истифодаи бот ба каналҳои зерин обуна шавед</b>\n\nБаъд аз обуна тугмаи «✅ Тафтиш»-ро пахш кунед.", chk="✅ Тафтиш", no="❌ Шумо ҳанӯз ба ҳамаи каналҳо обуна нашудаед!"),
 "ru": dict(t="🔒 <b>Для использования бота подпишитесь на каналы ниже</b>\n\nПосле подписки нажмите «✅ Проверить».", chk="✅ Проверить", no="❌ Вы ещё не подписались на все каналы!"),
 "en": dict(t="🔒 <b>Please subscribe to the channels below to use the bot</b>\n\nThen tap “✅ Check”.", chk="✅ Check", no="❌ You haven't subscribed to all channels yet!"),
}
SUB_OK = {}; SUB_WARNED = set()
async def sub_missing(uid, fresh=False):
    """Obuna bo'lmagan kanallar ro'yxati (bo'sh = hammasi joyida). Admin va sozlanmagan holatda doim bo'sh."""
    if not C.REQ_CHANNELS or uid == C.ADMIN_ID: return []
    if not fresh and time.time() - SUB_OK.get(uid, 0) < 120: return []
    miss = []
    for ch in C.REQ_CHANNELS:
        try:
            mb = await bot.get_chat_member(ch["id"], uid)
            if mb.status in ("left", "kicked") or (mb.status == "restricted" and getattr(mb, "is_member", True) is False): miss.append(ch)
        except Exception as e:   # bot kanalda admin emas / kanal topilmadi: foydalanuvchini qamamaymiz, adminga bir marta xabar beramiz
            logging.warning("sub check %s: %s", ch["id"], e)
            if ch["id"] not in SUB_WARNED:
                SUB_WARNED.add(ch["id"]); asyncio.create_task(admin_say(f"⚠️ Majburiy obuna: <code>{H.escape(str(ch['id']))}</code> kanalini tekshirib bo'lmadi. Bot shu kanalda ADMIN ekanini va REQUIRED_CHANNELS to'g'ri yozilganini tekshiring.\n<code>{H.escape(str(e))[:200]}</code>"))
    if not miss:
        if len(SUB_OK) > 20000: SUB_OK.clear()
        SUB_OK[uid] = time.time()
    return miss
def sub_kb(l, miss):
    rows = [[InlineKeyboardButton(text="📢 " + ch["name"], url=ch["url"])] for ch in miss if ch["url"].startswith("http")]
    rows.append([InlineKeyboardButton(text=_TS[l]["chk"], callback_data="chksub")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
async def gate(chat_id, uid, l):
    """True = obuna bor, davom etish mumkin. Aks holda obuna xabarini yuboradi va False qaytaradi."""
    l = l if l in _TS else "ru"
    miss = await sub_missing(uid, fresh=True)
    if not miss: return True
    await bot.send_message(chat_id, _TS[l]["t"], parse_mode="HTML", reply_markup=sub_kb(l, miss))
    return False

@dp.callback_query(F.data == "chksub")
async def chksub(c: CallbackQuery):
    l = lang_of(c.from_user.id); l = l if l in _TS else "ru"
    miss = await sub_missing(c.from_user.id, fresh=True)
    if miss:
        await c.answer(_TS[l]["no"], show_alert=True)
        try: await c.message.edit_reply_markup(reply_markup=sub_kb(l, miss))
        except Exception: pass
        return
    await c.answer()
    try: await c.message.delete()
    except Exception: pass
    await welcome(c.from_user.id, l)

@dp.message(CommandStart())
async def start(m: Message, command: CommandObject):
    u = D.user(m.from_user.id, m.from_user.full_name, command.args)
    if not u["lang_set"]: return await m.answer(PICK, reply_markup=picker())
    if await gate(m.chat.id, m.from_user.id, u["lang"]): await welcome(m.chat.id, u["lang"])

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
    if await gate(c.from_user.id, c.from_user.id, l): await welcome(c.from_user.id, l)

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
        await notify(o["uid"], "done", o); await post_channel(o["id"])
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
            o = D.q("SELECT * FROM orders WHERE id=?", (oid,)).fetchone(); done = True; await notify(o["uid"], "done", o); await post_channel(o["id"])
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
    await say_chunks(m, lines + ["", f"Ustama: +{cfg_markup() * 100:g}% · kurs: {cfg_rate():g}", "Topilmaganlar uchun: /dxcats so'z va /dxcat o'yin_id kategoriya"])

@dp.message(Command("dximport"))
async def dx_import_cmd(m: Message):
    if m.from_user.id != C.ADMIN_ID or not DX.enabled(): return
    await m.answer("🔄 Donatix'dagi barcha o'yinlar olinyapti (1-2 daqiqa ketishi mumkin)...")
    try: rep = await dx_import(True)
    except Exception as e:
        logging.exception("dximport"); return await m.answer(f"❌ xato: {e}")
    if "_" in rep: return await m.answer(rep["_"])
    await m.answer(f"✅ Yangi o'yinlar: {rep['new']} · yangilandi: {rep['upd']} · mahsulotlar: {rep['rows']} ta"
                   + (f"\n🗑 Avval o'chirilgan (o'tkazib yuborildi): {rep['skip']}" if rep["skip"] else "")
                   + "\n\nKerak bo'lmaganlarini Mini App → admin panel → o'yin → «O'chirish» bilan olib tashlang.")

@dp.message(Command("dxcat"))
async def dx_cat_set(m: Message, command: CommandObject):
    if m.from_user.id != C.ADMIN_ID: return
    a = (command.args or "").split()
    if len(a) != 2 or not any(x["id"] == a[0] for x in all_games()):
        return await m.answer("Ishlatish: /dxcat o'yin_id kategoriya_id\nO'yinlar: " + ", ".join(x["id"] for x in all_games()))
    D.dxgame_set(a[0], a[1], a[1]); await m.answer(f"✅ {a[0]} → {a[1]}. Endi /dxsync {a[0]} yozing.")

@dp.message(Command("dxraw"))
async def dx_raw(m: Message, command: CommandObject):
    if m.from_user.id != C.ADMIN_ID or not DX.enabled(): return
    p = (command.args or "").strip().lstrip("/")
    if not p or ".." in p: return await m.answer("Ishlatish: /dxraw glory/regions")
    p = urllib.parse.quote(p, safe="/?&=:,._-%+")   # kirill harflar ham ishlasin (q=клан)
    st, d = await DX.call("GET", "/" + p)
    await m.answer(H.escape(f"HTTP {st}\n" + json.dumps(d, ensure_ascii=False)[:3500]), parse_mode="HTML")

BK = {"changes": -1, "t": 0.0, "mid": None}
async def backup_db(force=False):
    """Baza o'zgargan bo'lsa (kamida 45 soniyada bir marta) nusxasini admin chatidagi qadalgan xabarga yangilaydi."""
    ch = D.db.total_changes
    if not force and (ch == BK["changes"] or time.time() - BK["t"] < 45): return False
    path = "/tmp/diavex-backup.db"; D.snapshot(path)
    name = "diavex-backup-" + datetime.now(timezone(timedelta(hours=C.TZ_HOURS))).strftime("%Y%m%d-%H%M") + ".db"
    cap = "💾 Baza zaxirasi. O'chirmang va qadalgan holda qoldiring: server qayta ishga tushganda balans va buyurtmalar shundan tiklanadi."
    mid = BK["mid"]
    if not mid:
        try:
            pm = getattr(await bot.get_chat(C.ADMIN_ID), "pinned_message", None)
            if pm and pm.document and str(pm.document.file_name or "").startswith("diavex-backup"): mid = pm.message_id
        except Exception: logging.warning("backup: qadalgan xabar topilmadi")
    sent = None
    if mid:
        try:
            await bot.edit_message_media(chat_id=C.ADMIN_ID, message_id=mid, media=InputMediaDocument(media=FSInputFile(path, filename=name), caption=cap)); sent = mid
        except Exception as e:
            if "not modified" in str(e).lower(): sent = mid
            else: logging.warning("backup: xabarni yangilab bo'lmadi (%s), yangisi yuboriladi", e)
    if not sent:
        msg = await bot.send_document(C.ADMIN_ID, FSInputFile(path, filename=name), caption=cap, disable_notification=True)
        try: await bot.pin_chat_message(C.ADMIN_ID, msg.message_id, disable_notification=True)
        except Exception: logging.exception("backup: qadab bo'lmadi")
        sent = msg.message_id
    BK.update(changes=ch, t=time.time(), mid=sent); return True
async def bk_worker():
    while True:
        try: await backup_db()
        except Exception: logging.exception("bk_worker")
        await asyncio.sleep(10)

@dp.message(Command("backup"))
async def backup_cmd(m: Message):
    if m.from_user.id != C.ADMIN_ID: return
    try: await backup_db(force=True); await m.answer("✅ Zaxira yangilandi (qadalgan xabarga qarang).")
    except Exception as e: await m.answer(f"❌ Zaxira xatosi: {H.escape(repr(e))[:300]}")

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
                miss = await sub_missing(u["id"])
                if miss: return web.json_response({"error": "sub", "channels": [{"name": x["name"], "url": x["url"]} for x in miss]}, status=403, headers=cors())
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

async def catalog(r): return web.json_response({**C.CATALOG, "games": public_catalog(), "bot": (await bot.me()).username, "support": C.SUPPORT, "rate": C.RATE, "pay": [{k: x[k] for k in ("id", "name", "type", "cur", "color", "icon")} for x in C.PAY]})
async def me(r):
    u = r["u"]; n = D.q("SELECT COUNT(*) c FROM users WHERE invited_by=?", (u["id"],)).fetchone()["c"]
    b = D.q("SELECT COUNT(*) c FROM users WHERE invited_by=? AND paid=1", (u["id"],)).fetchone()["c"]
    return web.json_response({"balance": round(u["balance"], 2), "spent": round(u["spent"], 2), "lang": u["lang"], "ref": u["ref"], "refs": n, "buyers": b, "bonus": round(u["bonus"], 2), "rating": rstats(), "admin": u["id"] == C.ADMIN_ID})
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
    gm = next((x for x in all_games() if x["id"] == gid), None)
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
CH_T = {
 "tg": dict(head="✅ <b>Фармоиш иҷро шуд!</b>", game="🎮 Бозӣ", prod="📦 Маҳсулот", pid="🆔 ID бозингар", nick="🎭 Никнейм", amt="💰 Маблағ", cur="сомонӣ", order="🏷 Фармоиш", user="👤 Корбар"),
 "ru": dict(head="✅ <b>Заказ выполнен!</b>", game="🎮 Игра", prod="📦 Товар", pid="🆔 ID игрока", nick="🎭 Никнейм", amt="💰 Сумма", cur="сомони", order="🏷 Заказ", user="👤 Пользователь"),
 "uz": dict(head="✅ <b>Buyurtma bajarildi!</b>", game="🎮 O'yin", prod="📦 Mahsulot", pid="🆔 O'yinchi ID", nick="🎭 Nik", amt="💰 Summa", cur="somoni", order="🏷 Buyurtma", user="👤 Foydalanuvchi"),
 "en": dict(head="✅ <b>Order completed!</b>", game="🎮 Game", prod="📦 Product", pid="🆔 Player ID", nick="🎭 Nickname", amt="💰 Amount", cur="TJS", order="🏷 Order", user="👤 User"),
}
def _mask(s, keep=3):
    s = str(s or ""); return s if len(s) <= keep * 2 else s[:keep] + "•" * (len(s) - keep * 2) + s[-keep:]
CH_WARN = {"t": 0.0}
def ch_target():
    v = C.ORDERS_CHANNEL
    return int(v) if re.fullmatch(r"-?\d+", v or "") else v
def ch_text(o, uname, uname_tg=""):
    """Kanalga yuboriladigan 'chek' matni: to'liq ID, ism, @username va oxirida Telegram ID; tepada va pastda chiziq."""
    t = CH_T.get(C.CH_LANG, CH_T["tg"]); e = H.escape
    pid = str(o["pid"] or ""); LINE = "━━━━━━━━━━━━━━━━━━"
    who = f"{e(str(uname or '—')[:30])}" + (f" (@{e(uname_tg)})" if uname_tg else "") + f" ({o['uid']})"
    L = [t["head"], LINE,
         f"{t['game']}: <b>{e(o['game'] or '')}</b>", f"{t['prod']}: <b>{e(o['item'] or o['title'] or '')}</b>",
         f"{t['pid']}: {e(pid)}"]
    if o["nick"]: L.append(f"{t['nick']}: <b>{e(o['nick'])}</b>")
    L += [f"{t['amt']}: <b>{o['price']:.2f} {t['cur']}</b>", f"{t['order']}: <b>#{o['id']}</b>", f"{t['user']}: {who}", LINE]
    return "\n".join(L)
async def post_channel(oid):
    """Bajarilgan buyurtmani kanalga yuboradi (kanal sozlanmagan bo'lsa hech narsa qilmaydi)."""
    if not C.ORDERS_CHANNEL: return
    try:
        o = D.q("SELECT o.*, u.name uname FROM orders o JOIN users u ON u.id=o.uid WHERE o.id=?", (oid,)).fetchone()
        if not o: return
        un = ""; nm = o["uname"]
        try:
            ch = await bot.get_chat(o["uid"]); un = ch.username or ""; nm = ch.full_name or nm
        except Exception: pass   # foydalanuvchi ma'lumotini olib bo'lmasa, bazadagi ismi bilan yuboriladi
        await bot.send_message(ch_target(), ch_text(o, nm, un), parse_mode="HTML", disable_notification=True)
    except Exception as e:
        logging.exception("kanalga yuborib bo'lmadi")
        if time.time() - CH_WARN["t"] > 3600:   # adminga soatiga bir marta xabar beramiz
            CH_WARN["t"] = time.time()
            await admin_say(f"⚠ Buyurtma #{oid} kanalga yuborilmadi: {H.escape(str(e))[:200]}\nBot kanalda admin va «xabar yuborish» huquqiga egami? ORDERS_CHANNEL to'g'rimi?")
@dp.message(Command("chtest"))
async def ch_test(m: Message):
    if m.from_user.id != C.ADMIN_ID: return
    if not C.ORDERS_CHANNEL: return await m.answer("ORDERS_CHANNEL yozilmagan (Render → Environment).")
    try:
        await bot.send_message(ch_target(), "✅ Test: kanal ulandi. Bajarilgan buyurtmalar shu yerga tushadi.", disable_notification=True)
        await m.answer("✅ Kanalga yuborildi. Ulanish to'g'ri.")
    except Exception as e: await m.answer(f"❌ Kanalga yuborib bo'lmadi: {H.escape(str(e))[:300]}\nBotni kanalga admin qiling (xabar yuborish huquqi bilan) va ORDERS_CHANNEL ni tekshiring.", parse_mode="HTML")

async def dx_done(oid):
    if D.order_finish(oid):
        o = D.q("SELECT * FROM orders WHERE id=?", (oid,)).fetchone()
        await notify(o["uid"], "done", o); await post_channel(o["id"])
        await admin_say(f"✅ Buyurtma #{oid} Donatix orqali avto bajarildi.")
async def dx_fail(oid, why):
    o = D.cancel_order(oid)   # pul mijozga qaytadi
    if o:
        await tell(o["uid"], "ordrej", no=oid, amt=f"{o['price']:.2f}")
        await admin_say(f"❌ Buyurtma #{oid} bajarilmadi: {H.escape(str(why))}\n💰 Pul mijozga qaytarildi.")
def cfg_rate():
    try:
        v = D.set_get("usd_tjs"); return float(v) if v not in (None, "") else C.USD_TJS
    except Exception: return C.USD_TJS
def cfg_markup():
    try:
        v = D.set_get("markup"); return float(v) / 100.0 if v not in (None, "") else C.DX_MARKUP
    except Exception: return C.DX_MARKUP
def final_catalog(include_hidden=False):
    """Mini App ko'radigan katalog = Donatix/catalog.json + admin o'zgartirishlari (narx, nom, yashirish, qo'shilgan mahsulot va region)."""
    ov = {r["item_id"]: r for r in D.ov_all()}; cust = D.cust_all(); regs = D.reg_all(); gh = D.ghide_all(); out = []
    tmv = D.tabmv_all(); tren = D.tabren_all()
    for g0 in dx_catalog():
        g = json.loads(json.dumps(g0)); gid = g["id"]; dyn = "kind" in g
        g["hidden"] = gid in gh; g["dx"] = dyn   # dx: Donatix orqali avto bajariladi (AUTO belgisi)
        if g["hidden"] and not include_hidden: continue
        hr = {r["region"] for r in regs if r["game_id"] == gid and r["hidden"]}
        if g.get("stars"):
            o = ov.get(g["stars"]["id"]); g["stars"]["auto"] = g["stars"]["unit"]
            if o and o["price"] is not None: g["stars"]["unit"] = o["price"]
            g["stars"]["hidden"] = bool(o and o["hidden"])
            if g["stars"]["hidden"] and not include_hidden: continue
        for tab in list(g["tabs"]):
            keep = []
            for it in g["tabs"][tab]:
                o = ov.get(it["id"]); it.update(src="dx" if dyn else "static", auto=it["price"], hidden=False, ov=False)
                if o:
                    if o["name"]: it["name"] = o["name"]
                    if o["price"] is not None: it["price"] = o["price"]; it["ov"] = True
                    it["hidden"] = bool(o["hidden"])
                if it.get("region") in hr: it["hidden"] = True
                if it["hidden"] and not include_hidden: continue
                keep.append(it)
            g["tabs"][tab] = keep
        for c in cust:
            if c["game_id"] != gid: continue
            it = {"id": f"c{c['id']}", "name": c["name"], "price": c["price"], "region": c["region"] or "", "src": "cust", "sku": c["sku"] or "", "auto": None, "ov": False,
                  "hidden": bool(c["hidden"]) or (c["region"] in hr)}
            if it["hidden"] and not include_hidden: continue
            g["tabs"].setdefault(c["tab"] or "📦", []).append(it)
        if not g.get("stars"):   # bo'lim nomlari va mahsulotni boshqa bo'limga ko'chirish (admin)
            rn = {r["old"]: r["new"] for r in tren if r["game_id"] == gid}; nt = {}; g["tabmap"] = {}
            for t0 in g["tabs"]: nt.setdefault(rn.get(t0, t0), []); g["tabmap"][t0] = rn.get(t0, t0)
            for t0, its in g["tabs"].items():
                for it in its:
                    it["tab0"] = rn.get(t0, t0); nt.setdefault(tmv.get(it["id"]) or it["tab0"], []).append(it)
            g["tabs"] = nt
        rl = list(g.get("regions") or []); tt = dict(g.get("region_titles") or {})
        for r_ in regs:
            if r_["game_id"] == gid:
                if r_["region"] not in rl: rl.append(r_["region"])
                if r_["title"]: tt[r_["region"]] = r_["title"]
        for items in g["tabs"].values():
            for it in items:
                if it.get("region") and it["region"] not in rl: rl.append(it["region"])
        if not include_hidden: rl = [x for x in rl if x not in hr]
        if rl: g["regions"] = rl; g["region_titles"] = tt
        g["hidden_regions"] = sorted(hr)
        if not include_hidden: g["tabs"] = {k: v for k, v in g["tabs"].items() if v} or ({"⭐": []} if g.get("stars") else {})
        out.append(g)
    return out
def info_list(gid): return [{"img": (f"/gi/{gid}/{b['pos']}?v={b['ver']}" if b["has"] else ""), "txt": b["txt"] or ""} for b in D.info_get(gid)]
def public_catalog():
    gs = final_catalog()
    for g in gs:
        for k in ("hidden", "hidden_regions", "tabmap"): g.pop(k, None)
        if g.get("stars"): g["stars"].pop("auto", None); g["stars"].pop("hidden", None)
        if g.get("infoblocks"): g["info"] = info_list(g["id"])
        for items in g["tabs"].values():
            for it in items:
                for k in ("src", "auto", "ov", "hidden", "sku", "tab0"): it.pop(k, None)
    return gs
def _admin(r): return r["u"]["id"] == C.ADMIN_ID
def admin_game_view(gid):
    fg = next((x for x in final_catalog(True) if x["id"] == gid), None)
    if not fg: return None
    items = []
    for tab, its in fg["tabs"].items():
        for it in its:
            items.append({"id": it["id"], "name": it["name"], "region": it.get("region") or "", "tab": tab, "price": it["price"], "auto": it.get("auto"), "ov": bool(it.get("ov")),
                          "hidden": bool(it.get("hidden")), "src": it["src"], "sku": it.get("sku", ""), "tab0": it.get("tab0", tab)})
    if fg.get("stars"):
        s = fg["stars"]; items.append({"id": s["id"], "name": "1 ⭐ (har bir star narxi)", "region": "", "tab": "⭐", "price": round(s["unit"], 4), "auto": round(s["auto"], 4),
                                       "ov": s["unit"] != s["auto"], "hidden": bool(s.get("hidden")), "src": "stars", "sku": ""})
    tt = fg.get("region_titles") or {}
    regions = [{"region": r_, "title": tt.get(r_, ""), "hidden": r_ in fg["hidden_regions"]} for r_ in (fg.get("regions") or [])]
    return {"id": fg["id"], "name": fg["name"], "icon": fg.get("icon", ""), "color": fg.get("color", "#334"), "hidden": fg["hidden"], "regions": regions, "items": items, "stars": bool(fg.get("stars")), "auto": bool(D.auto_get(gid)), "infoblocks": bool(fg.get("infoblocks")), "info": (info_list(gid) if fg.get("infoblocks") else []), "tabs": ([] if fg.get("stars") else list(fg["tabs"].keys()))}
async def admin_games(r):
    if not _admin(r): return web.json_response({"error": "forbidden"}, status=403)
    games = [{"id": g["id"], "name": g["name"], "icon": g.get("icon", ""), "color": g.get("color", "#334"), "hidden": g["hidden"],
              "count": sum(len(v) for v in g["tabs"].values()) + (1 if g.get("stars") else 0)} for g in final_catalog(True)]
    return web.json_response({"ok": True, "games": games, "settings": {"markup": round(cfg_markup() * 100, 2), "usd_tjs": cfg_rate()}})
async def admin_game_api(r):
    if not _admin(r): return web.json_response({"error": "forbidden"}, status=403)
    g = admin_game_view(str(r.query.get("id", "")))
    return web.json_response({"ok": True, "game": g}) if g else web.json_response({"error": "bad"})
async def admin_save(r):
    if not _admin(r): return web.json_response({"error": "forbidden"}, status=403)
    d = await r.json(); gid = str(d.get("game") or "")
    if gid and d.get("del_game"):   # o'yinni o'chirish (Donatix'dan qo'shilgan bo'lsa butunlay, asosiy bo'lsa yashiriladi)
        if D.auto_get(gid): D.auto_ban(gid); return web.json_response({"ok": True, "deleted": True})
        D.admin_apply(gid, [], [], [], [], True, {}); return web.json_response({"ok": True, "deleted": False})
    def num(x, lo, hi):
        try: v = float(x)
        except Exception: return None
        return round(v, 4) if lo <= v <= hi else None
    settings = {}
    st = d.get("settings") or {}
    if st:
        mk, rt = num(st.get("markup"), 0, 300), num(st.get("usd_tjs"), 0.01, 1000)
        if mk is None or rt is None: return web.json_response({"error": "bad", "msg": "Ustama 0–300, kurs 0.01–1000 bo'lishi kerak"})
        settings = {"markup": mk, "usd_tjs": rt}
    edits, adds, dels, regions, hide, tabren = [], [], [], [], None, []
    if gid:
        view = admin_game_view(gid)
        if not view: return web.json_response({"error": "bad"})
        known = {i["id"]: i for i in view["items"]}
        for e in (d.get("edits") or [])[:500]:
            iid = str(e.get("id") or ""); it = known.get(iid)
            if not it: continue
            x = {"id": iid}
            if "name" in e:
                nm = str(e["name"] or "").strip()[:60]
                if it["src"] == "cust" and not nm: return web.json_response({"error": "bad", "msg": "Qo'lda qo'shilgan mahsulot nomi bo'sh bo'lmasin"})
                if it["src"] != "stars": x["name"] = nm or None
            if e.get("reset"): x["reset"] = True
            elif "price" in e:
                lo = 0.001 if it["src"] == "stars" else 0.1
                p = num(e["price"], lo, 100000)
                if p is None: return web.json_response({"error": "bad", "msg": f"Narx noto'g'ri: {it['name']}"})
                x["price"] = p
            if "hidden" in e: x["hidden"] = bool(e["hidden"])
            if "tab" in e and it["src"] != "stars":
                tb = str(e["tab"] or "").strip()[:24]
                if tb and tb != it["tab"]: x["tab"] = tb; x["tab0"] = it.get("tab0")
            edits.append(x)
        for a in (d.get("adds") or [])[:100]:
            nm = str(a.get("name") or "").strip()[:60]; p = num(a.get("price"), 0.1, 100000)
            rg = str(a.get("region") or "").strip()[:20]; tb = str(a.get("tab") or "📦").strip()[:20] or "📦"; sku = str(a.get("sku") or "").strip()[:60]
            if not nm or p is None or (rg and not re.fullmatch(r"[\w .\-]+", rg)): return web.json_response({"error": "bad", "msg": "Yangi mahsulot ma'lumoti noto'g'ri"})
            adds.append({"name": nm, "price": p, "region": rg, "tab": tb, "sku": sku, "hidden": int(bool(a.get("hidden")))})
        cust_ids = {int(i["id"][1:]) for i in view["items"] if i["src"] == "cust"}
        dels = [int(x) for x in (d.get("dels") or []) if str(x).isdigit() and int(x) in cust_ids]
        for rg in (d.get("regions") or [])[:50]:
            nm = str(rg.get("region") or "").strip()[:20]
            if not re.fullmatch(r"[\w .\-]+", nm): return web.json_response({"error": "bad", "msg": "Region nomi noto'g'ri"})
            regions.append({"region": nm, "title": str(rg.get("title") or "").strip()[:30], "hidden": int(bool(rg.get("hidden")))})
        fgv = next((x for x in final_catalog(True) if x["id"] == gid), None) or {}
        tmap = fgv.get("tabmap") or {}
        for tr in (d.get("tabren") or [])[:30]:
            fr = str(tr.get("from") or "").strip(); to = re.sub(r"[\x00-\x1f]", "", str(tr.get("to") or "")).strip()[:24]
            if not fr or fr == to: continue
            if not to: return web.json_response({"error": "bad", "msg": "Bo'lim nomi bo'sh bo'lmasin"})
            ids = [i["id"] for i in view["items"] if i["tab"] == fr and i["src"] not in ("cust", "stars")]
            tabren.append({"from": fr, "to": to, "origs": [t0 for t0, t1 in tmap.items() if t1 == fr], "ids": ids})
        if "hide_game" in d: hide = bool(d["hide_game"])
    D.admin_apply(gid, edits, adds, dels, regions, hide, settings, tabren)
    return web.json_response({"ok": True})
def dx_price_tjs(usd, qty=1):
    """Donatix narxi (USD) -> bizning narx (somoni): kurs va ustama (standart +30%) bilan, 0.1 ga yuqoriga yaxlitlanadi."""
    return max(0.1, math.ceil(float(usd) * qty * cfg_rate() * (1 + cfg_markup()) * 10 - 1e-9) / 10)
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
PALETTE = ["#2563eb", "#7c3aed", "#db2777", "#ea580c", "#0f766e", "#4f46e5", "#b45309", "#0e7490"]
def all_games():
    """config.py dagi o'yinlar + /dximport bilan Donatix'dan qo'shilganlar."""
    base = list(C.DX_GAMES); ids = {g["id"] for g in base}; out = []
    for a in D.auto_all():
        if a["game_id"] in ids: continue
        out.append({"id": a["game_id"], "name": a["name"], "sub": "", "icon": "🎮", "color": PALETTE[sum(map(ord, a["game_id"])) % len(PALETTE)], "kind": "topup", "cat": "", "q": "", "auto": True})
    return base + sorted(out, key=lambda g: g["name"].lower())
def dx_rows(gm, prods, kind="topup"):
    """Donatix mahsulotlari -> dxcat qatorlari (region aniqlash bilan). (rows, manba)"""
    regs = [p_region(p) for p in prods]; src = "region" if any(regs) else ""
    if not any(regs):
        cats = [str(p.get("category_id") or "") for p in prods]
        if len(set(cats)) > 1:
            pre = os.path.commonprefix(cats)
            regs = [(c[len(pre):].strip("_- ") or str(p.get("category_name") or "")).upper() for c, p in zip(cats, prods)]; src = "kategoriya"
    if not any(regs):
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
        if k not in best or usd < best[k][7]: best[k] = row
    return list(best.values()), src
async def dx_import(create=True):
    """Donatix'dagi BARCHA top-up o'yinlarni oladi (config.py dagilardan tashqari). create=False: faqat mavjudlarini yangilaydi."""
    import collections
    if not cfg_rate(): return {"_": "USD_TJS yozilmagan (Render → Environment)"}
    prods = await DX.products(kind="topup", pages=40)
    cfgs = []
    for gm in C.DX_GAMES:
        if gm["kind"].startswith("telegram"): continue
        cf = D.dxgame_get(gm["id"]); cfgs.append((gm, (cf["cat"] if cf else "") or gm.get("cat", "")))
    prods = [p for p in prods if p.get("product_id") and p.get("category_id") and not any(dx_match(p, gm, cat, "") for gm, cat in cfgs)]
    if not prods: return {"new": 0, "upd": 0, "rows": 0, "skip": 0}
    base = lambda c: re.sub(r"_(?:[a-z]{2,3}|global|cis|latam|mena|sea|row)$", "", c)
    cnt = collections.Counter(base(str(p["category_id"])) for p in {str(p["category_id"]): p for p in prods}.values())
    groups = {}
    for p in prods:
        c = str(p["category_id"]); groups.setdefault(base(c) if cnt[base(c)] > 1 else c, []).append(p)
    old = {a["game_id"]: a for a in D.auto_all(True)}; rep = {"new": 0, "upd": 0, "rows": 0, "skip": 0}
    for key, ps in groups.items():
        gid = "g_" + (re.sub(r"[^a-z0-9_]", "", key.lower())[:30] or hashlib.md5(key.encode()).hexdigest()[:8])
        if gid in old and old[gid]["banned"]: rep["skip"] += 1; continue
        if gid not in old and not create: continue
        names = [re.sub(r"\s*[\(\[][^\)\]]{1,25}[\)\]]\s*$", "", str(p.get("category_name") or "")).strip() for p in ps]
        cn = collections.Counter(n for n in names if n)
        name = cn.most_common(1)[0][0] if cn else key
        if len(cn) > 1:
            pre = os.path.commonprefix(list(cn)).strip(" -_(")
            if len(pre) >= 3: name = pre
        rows, _src = dx_rows({"id": gid}, ps)
        if not rows: continue
        D.auto_set(gid, name, sorted({str(p["category_id"]) for p in ps}))
        D.dxcat_replace(gid, rows)
        rep["upd" if gid in old else "new"] += 1; rep["rows"] += len(rows)
    try: await dx_icons()
    except Exception: logging.exception("dx_icons")
    return rep

# ---------- O'YIN IKONKALARI (Donatix'dan avtomatik) ----------
from urllib.parse import urljoin
ICO_DIR = "/tmp/diavex-icons"
def img_of(d, depth=0):
    """Donatix javobidagi (mahsulot/kategoriya) rasm havolasini topadi."""
    if not isinstance(d, dict): return ""
    base = C.ICON_BASE.rstrip("/") + "/"
    def url(v):
        if isinstance(v, dict): v = v.get("url") or v.get("src") or ""
        if not isinstance(v, str) or not v.strip() or v.startswith("data:"): return ""
        v = v.strip()
        return urljoin(base, v) if v.startswith(("http", "/")) else urljoin(base, "/" + v)
    names = ("image", "image_url", "img", "icon", "icon_url", "logo", "logo_url", "picture", "thumbnail", "thumb", "cover", "photo", "category_image", "category_icon", "category_logo", "game_image", "game_icon")
    for k in names:
        u = url(d.get(k))
        if u: return u
    for k, v in d.items():
        if re.search(r"img|image|icon|logo|pic|thumb|cover", str(k), re.I):
            u = url(v)
            if u: return u
    if depth < 1:
        for k in ("category", "game"):
            u = img_of(d.get(k), depth + 1)
            if u: return u
    return ""
async def dx_icons():
    """Donatix'dagi o'yinlar rasmlarini topib, har bir avto-o'yinga bog'laydi. (bog'landi, jami, namuna kalitlari)"""
    prods = await DX.products(kind="topup", pages=40); cats = await DX.categories()
    by = {}
    for c in cats:
        u = img_of(c); cid = str(c.get("category_id") or c.get("id") or "")
        if u and cid: by[cid] = u
    for p in prods:
        u = img_of(p); cid = str(p.get("category_id") or "")
        if u and cid and cid not in by: by[cid] = u
    ok = tot = 0
    for a in D.auto_all():
        tot += 1
        try: cl = json.loads(a["cats"] or "[]")
        except Exception: cl = []
        u = next((by[c] for c in cl if c in by), "")
        if not u and C.ICON_TPL and cl: u = C.ICON_TPL.replace("{cat}", str(cl[0])).replace("{game}", a["game_id"])
        if u: D.icon_set(a["game_id"], u); ok += 1
    sample = ""
    if not ok:
        npi = sum(1 for p in prods if p.get("image_url")); nci = sum(1 for c in cats if c.get("image_url"))
        sample = f"image_url bor: mahsulot {npi}/{len(prods)}, kategoriya {nci}/{len(cats)}"
        ex = [(p.get("category_id"), p.get("image_url")) for p in prods if p.get("image_url")][:3]
        sample += "\nrasmli namunalar: " + repr(ex)
        if cats: sample += "\nkategoriya: " + json.dumps({k: (v if k != "products" else "...") for k, v in cats[0].items()}, ensure_ascii=False)[:500]
        if prods:
            st, d = await DX.call("GET", "/products/" + urllib.parse.quote(str(prods[0]["product_id"])))
            sample += f"\nmahsulot HTTP {st}: " + json.dumps(d, ensure_ascii=False)[:700]
    return ok, tot, sample
def _dl_icon(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; DiavexBot/1.0)", "Accept": "image/*"})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = r.read(2_000_001); ct = r.headers.get("Content-Type", "image/png").split(";")[0]
    if len(data) > 2_000_000 or not ct.startswith("image/"): raise ValueError("rasm emas")
    os.makedirs(ICO_DIR, exist_ok=True)
    open(path, "wb").write(data); open(path + ".ct", "w").write(ct)
async def ico(r):
    gid = re.sub(r"[^a-z0-9_]", "", r.match_info["g"].lower()); u = D.icon_get(gid)
    nz = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())
    gm = next((x for x in all_games() if x["id"] == gid), None)
    want = {nz(gid), nz(gid[2:] if gid.startswith("g_") else gid)} | ({nz(gm["name"])} if gm else set())
    loc = next((os.path.join(HERE, f) for f in os.listdir(HERE) if f.lower().endswith(".png") and nz(f[:-4]) in want), None)   # o'yin nomi.png yoki id.png
    if loc: return web.FileResponse(loc, headers={"Cache-Control": "public, max-age=3600"})
    path = os.path.join(ICO_DIR, gid)
    if not u or not u.startswith("https://"): return web.Response(status=404)
    if not os.path.exists(path):
        try: await asyncio.to_thread(_dl_icon, u, path)
        except Exception: logging.warning("icon %s: yuklab bo'lmadi", gid); return web.Response(status=404)
    ct = open(path + ".ct").read() if os.path.exists(path + ".ct") else "image/png"
    return web.Response(body=open(path, "rb").read(), content_type=ct, headers={"Cache-Control": "public, max-age=604800"})
@dp.message(Command("dxids"))
async def dx_ids(m: Message, command: CommandObject):
    if m.from_user.id != C.ADMIN_ID: return
    f = (command.args or "").strip().lower()
    rows = [f"<code>{H.escape(g['id'])}</code> — {H.escape(g['name'])}" for g in all_games() if not f or f in g["name"].lower() or f in g["id"]]
    if not rows: return await m.answer("Topilmadi. Ishlatish: /dxids call of duty")
    await say_chunks(m, rows[:60])
@dp.message(Command("dxico"))
async def dx_ico_set(m: Message, command: CommandObject):
    if m.from_user.id != C.ADMIN_ID: return
    a = (command.args or "").split()
    if len(a) != 2 or not a[1].startswith("https://") or not any(x["id"] == a[0] for x in all_games()):
        return await m.answer("Ishlatish: /dxico o'yin_id https://rasm-havolasi.png")
    D.icon_set(a[0], a[1]); p = os.path.join(ICO_DIR, a[0])
    for f in (p, p + ".ct"):
        if os.path.exists(f): os.remove(f)
    await m.answer(f"✅ {a[0]} uchun rasm saqlandi.")
@dp.message(Command("dxicons"))
async def dx_icons_cmd(m: Message):
    if m.from_user.id != C.ADMIN_ID or not DX.enabled(): return
    await m.answer("🖼 Ikonkalar olinyapti...")
    ok, tot, sample = await dx_icons()
    for f in os.listdir(ICO_DIR) if os.path.isdir(ICO_DIR) else []: os.remove(os.path.join(ICO_DIR, f))   # eski keshni tozalaydi
    await m.answer(f"✅ Rasm bog'landi: {ok} / {tot}" + (f"\n⚠ Donatix javobida rasm havolasi topilmadi.\n<code>{H.escape(sample)}</code>\nShu xabarni menga yuboring." if not ok else ""), parse_mode="HTML")

async def dx_sync(only=None):
    """Donatix'dan o'yinlar va paketlarni oladi (miqdorlari Donatix'dagidek, region bo'yicha). {o'yin_id: (soni, regionlar, namuna, manba) | xato matni}"""
    rep = {}
    if not cfg_rate(): return {"_": "USD_TJS yozilmagan (Render → Environment)"}
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
    for gm in all_games():
        rows = D.dxcat_items(gm["id"])
        if not rows or not cfg_rate(): continue
        kind = gm["kind"]; tg = kind.startswith("telegram")
        try: fl = json.loads(rows[0]["fields"] or "[]")
        except Exception: fl = []
        if not fl: fl = [{"key": "telegram_username" if tg else "player_id"}]
        g = {"id": gm["id"], "name": gm["name"], "sub": gm.get("sub", ""), "icon": gm.get("icon", "🎮"), "color": gm.get("color", "#334"), "kind": kind,
             "fields": [{"key": f.get("key"), "label": f.get("label") or ""} for f in fl if f.get("key") and re.fullmatch(r"\w+", str(f.get("key")))], "nocheck": tg, "tabs": {}}
        if kind == "telegram_stars":
            r = rows[0]; lo, hi = r["qmin"] or 50, r["qmax"] or 10000
            g["stars"] = {"id": r["product_id"], "unit": r["price_usd"] * cfg_rate() * (1 + cfg_markup()), "min": lo, "max": hi, "presets": [p for p in (50, 100, 250, 500, 1000, 2500, 5000) if lo <= p <= hi] or [lo]}
            g["tabs"] = {"⭐": []}
        else:
            regs = []
            for r in rows:
                if r["region"] and r["region"] not in regs: regs.append(r["region"])
                g["tabs"].setdefault(r["tab"], []).append({"id": r["product_id"], "name": r["name"], "price": dx_price_tjs(r["price_usd"]), "region": r["region"]})
            regs.sort(key=lambda x: (0 if x.upper() == "CIS" else 1 if x.upper() == "GLOBAL" else 2, x))
            if regs: g["regions"] = regs; g["region_titles"] = {r["region"]: r["region_title"] for r in rows if r["region"]}
        dyn[gm["id"]] = g
    cfg_ids = {x["id"] for x in C.DX_GAMES}
    return ([dyn[x["id"]] for x in all_games() if x["id"] in dyn and x["id"] in cfg_ids] + [x for x in C.CATALOG["games"] if x["id"] not in dyn]
            + [dyn[x["id"]] for x in all_games() if x["id"] in dyn and x["id"] not in cfg_ids])
def dx_find(gid, iid):
    gm = next((x for x in all_games() if x["id"] == gid), None); r = D.dxcat_get(str(iid or ""))
    return (gm, r) if gm and r and r["game_id"] == gid and cfg_rate() else None
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
        if cfg_rate():
            try: cost = float(prod.get("price_usd")) * (qty or 1) * cfg_rate()
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
                    for gid in D.dxcat_game_ids():
                        if not gid.startswith("g_"): await dx_sync(gid)
                    await dx_import(create=False)
                if time.time() - last_bal > 600:
                    last_bal = time.time(); b = await DX.balance()
                    if b is not None and b < C.DX_MIN_BALANCE and time.time() - warned > 6 * 3600:
                        warned = time.time(); await admin_say(f"⚠ Donatix balansi kam: ${b:.2f}. To'ldiring, aks holda buyurtmalar qo'lda keladi.")
        except Exception: logging.exception("dx_worker")
        await asyncio.sleep(8)
async def order(r):
    d = await r.json(); uid = r["u"]["id"]; tg = r["tg"]
    gid = str(d.get("game") or ""); iid = str(d.get("item") or "")
    fg = next((x for x in final_catalog() if x["id"] == gid), None)   # admin o'zgartirishlari bilan (narx, yashirin mahsulot)
    if not fg: return web.json_response({"error": "bad"})
    stars = bool(fg.get("stars")) and fg["stars"]["id"] == iid
    it = None if stars else next((i for items in fg["tabs"].values() for i in items if i["id"] == iid), None)
    if not stars and not it: return web.json_response({"error": "bad"})
    if fg.get("clan") and d.get("ack") is not True: return web.json_response({"error": "bad"})   # klan xizmati: mijoz shartlarga rozi bo'lishi shart
    src = "stars" if stars else it["src"]
    nick = ""; qty = 1; fj = ""; sku = None
    if src in ("dx", "stars"):   # Donatix'dan olingan mahsulot
        dyn = dx_find(gid, iid)
        if not dyn: return web.json_response({"error": "bad"})
        gm, row = dyn; kind = row["kind"]
        try: fl = [f.get("key") for f in json.loads(row["fields"] or "[]") if f.get("key")]
        except Exception: fl = []
        fields = parse_fields(d.get("fields"), fl or ["telegram_username" if kind.startswith("telegram") else "player_id"])
        if not fields: return web.json_response({"error": "bad"})
        if stars:
            try: qty = int(d.get("qty"))
            except Exception: return web.json_response({"error": "bad"})
            if not (row["qmin"] <= qty <= row["qmax"]): return web.json_response({"error": "bad"})
            price = max(0.1, math.ceil(fg["stars"]["unit"] * qty * 10 - 1e-9) / 10)
        else: price = it["price"]
        region = row["region"] or ""
        gname = fg["name"]; iname = (it["name"] if it else row["name"]) + (f" × {qty}" if stars else "")
        product = iname + (f" [{region}]" if region else ""); pid = " / ".join(fields.values())
        if not kind.startswith("telegram"):
            st, nick = await dx_check_fields(gm["id"], row["product_id"], fields)
            if st == "noid": return web.json_response({"error": "noid"})
        sku = row["product_id"] if (DX.enabled() and DXSTATE["on"]) else None
        fj = json.dumps(fields, ensure_ascii=False)
    elif src == "cust":   # admin qo'lda qo'shgan mahsulot (sku bo'lsa Donatix orqali avto)
        fields = parse_fields(d.get("fields"), [f["key"] for f in (fg.get("fields") or []) if f.get("key")] or ["player_id"])
        if not fields: return web.json_response({"error": "bad"})
        region = it.get("region") or ""; gname = fg["name"]; iname = it["name"]; price = it["price"]; stars = False
        product = iname + (f" [{region}]" if region else ""); pid = " / ".join(fields.values())
        sku = it.get("sku") or None
        if sku and not (DX.enabled() and DXSTATE["on"]): sku = None
        fj = json.dumps(fields, ensure_ascii=False)
    else:   # catalog.json dagi mahsulot
        pid = str(d.get("pid") or "").strip()
        if not (pid.isdigit() and 5 <= len(pid) <= 14): return web.json_response({"error": "bad"})
        rl = fg.get("regions") or []
        region = d.get("region") if d.get("region") in rl else (rl[0] if rl else "")
        gname = fg["name"]; iname = it["name"]; price = it["price"]; stars = False
        product = iname + (f" [{region}]" if region else "")
        sg = next((x for x in C.CATALOG["games"] if x["id"] == gid), {}); rr = region if region in (sg.get("regions") or []) else ""
        st, nick = ("unv", "") if fg.get("clan") else await check_id(gid, pid, rr)   # ID ni server o'zi tekshiradi (klan ID ni tekshirib bo'lmaydi)
        if st == "noid": return web.json_response({"error": "noid"})
        sku = dx_resolve(iid, rr); fields = {"player_id": pid}   # Donatix'ga bog'langan bo'lsa avto
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

# ---------- MIJOZ PROFIL RASMI ----------
AVMAP = {}; AV_DIR = "/tmp/diavex-av"
def av_tok(uid):
    """Telegram ID ni ko'rsatmaydigan yopiq havola (token -> uid xotirada saqlanadi)."""
    t = hmac.new(C.BOT_TOKEN.encode(), f"av{uid}".encode(), hashlib.sha256).hexdigest()[:16]
    AVMAP[t] = uid; return "/av/" + t
async def avatar(r):
    uid = AVMAP.get(r.match_info["t"])
    if not uid: return web.Response(status=404)
    path = os.path.join(AV_DIR, str(uid))
    if not (os.path.exists(path) and time.time() - os.path.getmtime(path) < 6 * 3600):
        data = b""
        try:
            ph = await bot.get_user_profile_photos(uid, limit=1)
            if ph.total_count and ph.photos:
                import io
                buf = io.BytesIO(); sz = ph.photos[0]; await bot.download(sz[min(1, len(sz) - 1)].file_id, destination=buf); data = buf.getvalue()
        except Exception: logging.warning("avatar %s: olib bo'lmadi", uid)
        os.makedirs(AV_DIR, exist_ok=True); open(path, "wb").write(data)
    data = open(path, "rb").read()
    if not data: return web.Response(status=404)
    return web.Response(body=data, content_type="image/jpeg", headers={"Cache-Control": "public, max-age=3600"})
async def reviews(r):
    rows = D.q("SELECT r.oid, r.stars, r.text, r.reply, r.ts, o.game, o.item, o.title, u.name, u.id uid FROM ratings r JOIN orders o ON o.id=r.oid JOIN users u ON u.id=r.uid ORDER BY r.oid DESC LIMIT 300").fetchall()
    dt = lambda s: f"{s[8:10]}.{s[5:7]}.{s[:4]}" if s else ""
    items = [{"id": x["oid"], "name": (x["name"] or "?")[:20], "stars": x["stars"], "game": x["game"] or "", "item": x["item"] or x["title"], "text": x["text"] or "", "reply": x["reply"] or "", "date": dt(x["ts"]), "av": av_tok(x["uid"])} for x in rows]
    return web.json_response({**rstats(), "items": items})
async def top_api(r):
    kind = r.query.get("kind", "donors"); cut = {"week": "-7 days", "month": "-30 days"}.get(r.query.get("period", "week"))
    a = (cut,) if cut else ()
    if kind == "topups":
        w = "AND f.ts >= datetime('now', ?)" if cut else ""
        rows = D.q(f"SELECT u.id uid, u.name, SUM(f.amount) s FROM fin f JOIN users u ON u.id=f.uid WHERE f.title='Top up' {w} GROUP BY f.uid ORDER BY s DESC LIMIT 20", a)
    else:
        w = "AND o.ts >= datetime('now', ?)" if cut else ""
        rows = D.q(f"SELECT u.id uid, u.name, SUM(o.price) s FROM orders o JOIN users u ON u.id=o.uid WHERE o.status!='cancelled' {w} GROUP BY o.uid ORDER BY s DESC LIMIT 20", a)
    return web.json_response({"items": [{"name": (x["name"] or "?")[:20], "total": round(x["s"] or 0, 2), "av": av_tok(x["uid"])} for x in rows]})
async def history(r):
    uid = r["u"]["id"]; f = lambda x: (lambda s: f"{s[8:10]}.{s[5:7]}.{s[:4]} {s[11:16]}" if len(s) >= 16 else s)(str(x or ""))
    o = [{"id": x["id"], "title": x["title"], "price": x["price"], "status": x["status"], "date": f(x["ts"]), "game": x["game"] or "", "item": x["item"] or ""} for x in D.q("SELECT * FROM orders WHERE uid=? ORDER BY id DESC LIMIT 50", (uid,))]
    n = [{"title": x["title"], "amount": x["amount"], "date": f(x["ts"])} for x in D.q("SELECT * FROM fin WHERE uid=? ORDER BY id DESC LIMIT 50", (uid,))]
    return web.json_response({"orders": o, "fin": n})

async def admin_info_save(r):
    if not _admin(r): return web.json_response({"error": "forbidden"}, status=403)
    d = await r.json(); gid = str(d.get("game") or "")
    if not any(x["id"] == gid and x.get("infoblocks") for x in C.CATALOG["games"]): return web.json_response({"error": "bad", "msg": "Bu o'yinda rasm/tavsif yo'q"})
    old = {b["pos"]: D.info_img(gid, b["pos"]) for b in D.info_get(gid)}; out = []
    for b in (d.get("blocks") or [])[:8]:
        txt = str(b.get("txt") or "")[:2000].strip(); img = str(b.get("img") or ""); blob = None
        if img.startswith("data:image/"):
            try: raw = base64.b64decode(img.split(",", 1)[1])
            except Exception: raw = b""
            if not raw or len(raw) > 1_500_000 or not (raw[:3] == b"\xff\xd8\xff" or raw[:4] == b"\x89PNG" or raw[:4] == b"RIFF"):
                return web.json_response({"error": "bad", "msg": "Rasm noto'g'ri yoki juda katta"})
            blob = raw
        elif img.startswith("keep:"):
            try: blob = (old.get(int(img[5:])) or (None,))[0]
            except Exception: blob = None
        if blob or txt: out.append((txt, blob))
    D.info_set(gid, out)
    return web.json_response({"ok": True})
async def info_img(r):
    try: row = D.info_img(r.match_info["g"], int(r.match_info["p"]))
    except Exception: return web.Response(status=404)
    if not row or not row[0]: return web.Response(status=404)
    b = row[0]; ct = "image/jpeg" if b[:3] == b"\xff\xd8\xff" else "image/png" if b[:4] == b"\x89PNG" else "image/webp"
    return web.Response(body=b, content_type=ct, headers={"Cache-Control": "public, max-age=31536000, immutable"})
def _img(path):
    async def h(r):
        return web.FileResponse(path) if os.path.exists(path) else web.Response(status=404)
    return h
async def main():
    app = web.Application(middlewares=[mw], client_max_size=8 * 1024 * 1024)
    app.on_response_prepare.append(_sec)
    app.add_routes([web.get("/api/catalog", catalog), web.get("/api/me", me), web.post("/api/lang", lang), web.post("/api/order", order),
                    web.post("/api/topup", topup), web.post("/api/receipt", receipt_api), web.get("/api/history", history), web.get("/api/top", top_api), web.get("/api/checkid", checkid), web.get("/api/admin/games", admin_games), web.get("/api/admin/game", admin_game_api), web.post("/api/admin/save", admin_save), web.post("/api/admin/info", admin_info_save), web.get("/gi/{g}/{p}", info_img), web.get("/api/reviews", reviews), web.route("OPTIONS", "/{p:.*}", lambda r: web.Response()),
                    web.get("/", lambda r: web.FileResponse(os.path.join(HERE, "index.html")))])
    for f in ("style.css", "app.js", "i18n.js", "ru.json", "uz.json", "tg.json", "en.json", "logo.png", "splash.jpg"):
        app.router.add_get("/" + f, lambda r, f=f: web.FileResponse(os.path.join(HERE, f)))
    for g in C.CATALOG["games"]:
        app.router.add_get("/" + g["id"] + ".png", _img(os.path.join(HERE, g["id"] + ".png")))
    _have = {g["id"] for g in C.CATALOG["games"]}
    for g in C.DX_GAMES:
        if g["id"] not in _have:
            app.router.add_get("/" + g["id"] + ".png", _img(os.path.join(HERE, g["id"] + ".png")))
    app.router.add_get("/ico/{g}", ico); app.router.add_get("/av/{t}", avatar)
    for x in C.PAY:
        app.router.add_get("/" + x["id"] + ".png", _img(os.path.join(HERE, x["id"] + ".png")))
    run = web.AppRunner(app); await run.setup(); await web.TCPSite(run, "0.0.0.0", C.PORT).start()
    _t = asyncio.create_task(dx_worker()); TASKS.add(_t)
    _b = asyncio.create_task(bk_worker()); TASKS.add(_b)
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())
