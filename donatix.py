"""Donatix API mijozi (https://donatix.tj/api/v1). Kalit faqat Render'dagi DONATIX_KEY da turadi."""
import asyncio, json, logging, time, urllib.request, urllib.error
import config as C

_CACHE = {}; LAST = {}
def enabled(): return bool(C.DONATIX_KEY)

def _req(method, path, body, headers):
    h = {"X-API-Key": C.DONATIX_KEY, "Accept": "application/json", "User-Agent": "Mozilla/5.0 (compatible; DiavexBot/1.0)", **headers}
    data = None
    if body is not None:
        data = json.dumps(body).encode(); h["Content-Type"] = "application/json"
    req = urllib.request.Request(C.DONATIX_URL + path, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=30) as r: return r.status, r.read(400_000)
    except urllib.error.HTTPError as e:
        return e.code, e.read(400_000)

async def call(method, path, body=None, headers=None):
    """(http_status, json yoki None). 0 = tarmoq xatosi / timeout (natija noaniq)."""
    try: st, raw = await asyncio.to_thread(_req, method, path, body, headers or {})
    except Exception as e:
        logging.warning("donatix network error: %s", e); return 0, None
    try: data = json.loads(raw.decode("utf-8", "replace"))
    except Exception: data = None
    if st != 200 or (isinstance(data, dict) and data.get("ok") is False):
        LAST["err"] = (method, path.split("?")[0], st, err_code(data), str((data or {}).get("error") or "")[:160] if isinstance(data, dict) else raw[:120].decode("utf-8", "replace"))
    return st, data

def err_code(d):
    return str((d or {}).get("code") or "") if isinstance(d, dict) else ""

async def balance():
    st, d = await call("GET", "/balance")
    try: return float(d["balance"]) if st == 200 and d and d.get("ok") else None
    except Exception: return None

async def categories():
    st, d = await call("GET", "/categories")
    if st != 200 or not d: return []
    return d.get("items") or d.get("categories") or []

async def products(category=None, q=None, kind="topup", limit=500, pages=4):
    out = []
    for p in range(pages):
        path = f"/products?kind={kind}&limit={limit}&offset={p * limit}"
        if category: path += f"&category_id={urllib.request.quote(category)}"
        if q: path += f"&q={urllib.request.quote(q)}"
        st, d = await call("GET", path)
        items = (d or {}).get("items") or []
        if st != 200 or not items: break
        out += items
        if len(items) < limit: break
    return out

async def product(pid, fresh=False):
    """Bitta mahsulot (5-15 daqiqa keshlanadi). None = topilmadi/xato."""
    c = _CACHE.get(pid)
    if c and not fresh and time.time() - c[0] < 600: return c[1]
    st, d = await call("GET", f"/products/{urllib.request.quote(pid)}")
    p = None
    if st == 200 and isinstance(d, dict) and d.get("ok"):
        p = d.get("product") or d.get("item") or ((d.get("items") or [None])[0])
    if p: _CACHE[pid] = (time.time(), p)
    return p

async def account_check(sku, fields):
    """('ok', nik) | ('noid', '') | ('unv', ''). fields: dict yoki oddiy player_id matni."""
    if not isinstance(fields, dict): fields = {"player_id": str(fields)}
    st, d = await call("POST", "/accounts/check", {"product_id": sku, "fields": fields})
    if st == 200 and d and d.get("ok"):
        if d.get("supported") is False: return "unv", ""
        if d.get("valid") is True: return "ok", str(d.get("player_name") or "")[:40]
        if d.get("valid") is False: return "noid", ""
    if st == 400 and err_code(d) in ("player_not_found", "account_not_found"): return "noid", ""
    return "unv", ""

async def create_order(sku, fields, key, qty=None):
    if not isinstance(fields, dict): fields = {"player_id": str(fields)}
    body = {"product_id": sku, "fields": fields}
    if qty: body["quantity"] = qty
    return await call("POST", "/orders", body, {"Idempotency-Key": key})

async def order_status(dx_id):
    return await call("GET", f"/orders/{urllib.request.quote(str(dx_id))}")

def hint(st, code=""):
    if st == 0: return "Donatix'ga ulanib bo'lmadi (tarmoq xatosi yoki manzil noto'g'ri). DONATIX_URL ni tekshiring."
    if st == 401: return "Kalit noto'g'ri, to'liq emas yoki o'chirilgan. Donatix'da «Скопировать» bilan kalitni TO'LIQ nusxalab, Render'dagi DONATIX_KEY ni almashtiring."
    if st == 403: return "Kirish taqiqlangan (hisob/IP bloklangan yoki himoya tizimi)."
    if st == 429: return "So'rovlar ko'p yoki IP vaqtincha bloklangan. 15 daqiqa kuting."
    if st >= 500: return "Donatix serverida muammo, keyinroq urinib ko'ring."
    return "Javob kutilgan ko'rinishda emas."
def last_error_text():
    e = LAST.get("err")
    if not e: return ""
    m, p, st, code, msg = e
    return f"{m} {p} → HTTP {st} {code} {msg}".strip()
