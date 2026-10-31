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
