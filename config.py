import os, json
from dotenv import load_dotenv
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
MINIAPP_URL = os.getenv("MINIAPP_URL", "")
ORIGIN = os.getenv("ALLOWED_ORIGIN", "*")
PORT = int(os.getenv("PORT", "8080"))
CARD = os.getenv("CARD_NUMBER", "")
HOLDER = os.getenv("CARD_HOLDER", "")
SUPPORT = os.getenv("SUPPORT_USERNAME", "")
REF_PERCENT = 2  # referal bonus, %
CATALOG = json.load(open(os.path.join(os.path.dirname(__file__), "catalog.json"), encoding="utf-8"))
def find_item(game_id, item_id):
    for g in CATALOG["games"]:
        if g["id"] == game_id:
            for items in g["tabs"].values():
                for i in items:
                    if i["id"] == item_id:
                        return g, i
    return None, None

RATE = float(os.getenv("RUB_RATE", "0.108"))  # 1 RUB = RATE somoni
DC_PHONE = os.getenv("DC_PHONE", "")
DC_HOLDER = os.getenv("DC_HOLDER", HOLDER)
# Faqat DC Next (chek bilan). Telefon DC_PHONE da; bo'lmasa CARD_NUMBER ishlatiladi.
PAY = []
if DC_PHONE:
    PAY.append({"id": "dc", "name": "DC Next", "type": "phone", "value": DC_PHONE, "holder": DC_HOLDER, "cur": "TJS", "color": "#e8590c", "icon": "DC"})
elif CARD:
    PAY.append({"id": "dc", "name": "DC Next", "type": "card", "value": CARD, "holder": HOLDER, "cur": "TJS", "color": "#e8590c", "icon": "DC"})

def _url(v):
    v = v.strip()
    return "https://t.me/" + v[1:] if v.startswith("@") else v
CHANNEL_URL = _url(os.getenv("CHANNEL_URL", ""))   # yangiliklar kanali (https://t.me/... yoki @kanal)
LESSONS_URL = _url(os.getenv("LESSONS_URL", ""))   # darslar havolasi

TZ_HOURS = float(os.getenv("TZ_HOURS", "5"))  # admin xabarlaridagi vaqt (UTC+5)

# --- O'yinchi ID ni tekshirish (yetkazib beruvchi API'si, ixtiyoriy) ---
# IDCHECK_URL misol: https://api.provider.com/check?game={game}&uid={id}&region={region}&key=SIZNING_KALIT
IDCHECK_URL = os.getenv("IDCHECK_URL", "").strip()
def _jenv(name):
    try: return json.loads(os.getenv(name, "") or "{}")
    except Exception: return {}
IDCHECK_GAMES = _jenv("IDCHECK_GAMES")      # {"freefire":"ff","pubg":"pubgm"} (bizning o'yin id -> ularning kodi)
IDCHECK_HEADERS = _jenv("IDCHECK_HEADERS")  # {"Authorization":"Bearer ..."} kerak bo'lsa
IDCHECK_NICK = os.getenv("IDCHECK_NICK", "nickname")  # javobdagi nik joyi, masalan data.nickname

# --- Donatix (avto yetkazib berish) ---
DONATIX_KEY = os.getenv("DONATIX_KEY", "").strip()          # faqat Render Environment'da!
DONATIX_URL = os.getenv("DONATIX_URL", "https://donatix.tj/api/v1").rstrip("/")
USD_TJS = float(os.getenv("USD_TJS", "0") or 0)             # 1 USD = ? somoni (tannarx tekshiruvi uchun, ixtiyoriy)
DX_MIN_BALANCE = float(os.getenv("DX_MIN_BALANCE", "5") or 5)  # Donatix balansi shundan kam bo'lsa ogohlantiradi (USD)
DX_CATEGORIES = {"freefire": "free_fire", "pubg": "pubg_mobile", "mlbb": "mobile_legends", **_jenv("DX_CATEGORIES")}
DX_QUERIES = {"freefire": "ff", "pubg": "pubg", "mlbb": "mobile legends", **_jenv("DX_QUERIES")}   # Donatix qidiruv so'zi (o'yin id -> matn)

DX_MARKUP = float(os.getenv("DX_MARKUP", "27") or 27) / 100.0   # Donatix narxiga ustama, % (standart 27)
_DXG = [
 {"id": "freefire", "name": "FREE FIRE", "sub": "Diamonds & Pass", "icon": "🔥", "color": "#1d4ed8", "kind": "topup", "cat": "free_fire", "q": "ff"},
 {"id": "pubg", "name": "PUBG MOBILE", "sub": "UC", "icon": "🪖", "color": "#3b6ea5", "kind": "topup", "cat": "pubg_mobile", "q": "pubg mobile"},
 {"id": "mlbb", "name": "MOBILE LEGENDS", "sub": "Diamonds", "icon": "⚔️", "color": "#7c3aed", "kind": "topup", "cat": "mobile_legends", "q": "mobile legends"},
 {"id": "coc", "name": "CLASH OF CLANS", "sub": "Gems", "icon": "🏰", "color": "#b45309", "kind": "topup", "cat": "clash_of_clans", "q": "clash of clans"},
 {"id": "tgpremium", "name": "TELEGRAM PREMIUM", "sub": "3 · 6 · 12", "icon": "💎", "color": "#2563eb", "kind": "telegram_premium"},
 {"id": "tgstars", "name": "TELEGRAM STARS", "sub": "Stars", "icon": "⭐", "color": "#f59e0b", "kind": "telegram_stars"},
]
try: DX_GAMES = json.loads(os.getenv("DX_GAMES", "") or "null") or _DXG
except Exception: DX_GAMES = _DXG

# --- Chekni AI bilan tekshirish (ixtiyoriy) ---
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
AI_MODEL = os.getenv("AI_MODEL", "claude-haiku-5-5").strip()
AI_URL = os.getenv("AI_URL", "https://api.anthropic.com/v1/messages").strip()
GEMINI_KEY = os.getenv("GEMINI_KEY", "").strip()   # bepul Gemini kaliti; qo'yilsa AI shu orqali ishlaydi (Claude kaliti o'rniga)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest").strip()
