import sqlite3, secrets, threading
_l = threading.Lock()
import logging, persist
logging.warning("baza: %s", persist.restore("data.db"))   # yangi deploydan keyin zaxiradan tiklaydi
db = sqlite3.connect("data.db", check_same_thread=False, isolation_level=None)
db.row_factory = sqlite3.Row
for _p in ("PRAGMA journal_mode=WAL", "PRAGMA synchronous=NORMAL", "PRAGMA busy_timeout=5000"):
    try: db.execute(_p)
    except sqlite3.Error: pass
db.executescript("""
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT,lang TEXT DEFAULT 'ru',balance REAL DEFAULT 0,spent REAL DEFAULT 0,ref TEXT,invited_by INTEGER,paid INTEGER DEFAULT 0,bonus REAL DEFAULT 0);
CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT,uid INTEGER,title TEXT,pid TEXT,price REAL,status TEXT DEFAULT 'pending',ts DATETIME DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS topups(id INTEGER PRIMARY KEY AUTOINCREMENT,uid INTEGER,amount REAL,status TEXT DEFAULT 'pending',ts DATETIME DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS ratings(oid INTEGER PRIMARY KEY,uid INTEGER,stars INTEGER);
CREATE TABLE IF NOT EXISTS dxmap(item_id TEXT,region TEXT,product_id TEXT,PRIMARY KEY(item_id,region));
CREATE TABLE IF NOT EXISTS dxcat(product_id TEXT PRIMARY KEY,game_id TEXT,region TEXT,region_title TEXT,name TEXT,tab TEXT,emoji TEXT,price_usd REAL,fields TEXT,kind TEXT,sort INTEGER,qmin INTEGER,qmax INTEGER,active INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS dxgames(game_id TEXT PRIMARY KEY,cat TEXT,q TEXT);
CREATE TABLE IF NOT EXISTS rhash(h TEXT PRIMARY KEY,tid INTEGER);
CREATE TABLE IF NOT EXISTS settings(k TEXT PRIMARY KEY,v TEXT);
CREATE TABLE IF NOT EXISTS catover(item_id TEXT PRIMARY KEY,name TEXT,price REAL,hidden INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS catcust(id INTEGER PRIMARY KEY AUTOINCREMENT,game_id TEXT,region TEXT,tab TEXT,name TEXT,price REAL,sku TEXT DEFAULT '',hidden INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS catregion(game_id TEXT,region TEXT,title TEXT,hidden INTEGER DEFAULT 0,PRIMARY KEY(game_id,region));
CREATE TABLE IF NOT EXISTS gamehide(game_id TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS cattab(item_id TEXT PRIMARY KEY,tab TEXT);
CREATE TABLE IF NOT EXISTS gameinfo(game_id TEXT,pos INTEGER,img BLOB,txt TEXT,ver INTEGER,PRIMARY KEY(game_id,pos));
CREATE TABLE IF NOT EXISTS autogames(game_id TEXT PRIMARY KEY,name TEXT,cats TEXT,banned INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS cattabname(game_id TEXT,old TEXT,new TEXT,PRIMARY KEY(game_id,old));
CREATE TABLE IF NOT EXISTS gameicon(game_id TEXT PRIMARY KEY,url TEXT);
CREATE TABLE IF NOT EXISTS fin(id INTEGER PRIMARY KEY AUTOINCREMENT,uid INTEGER,title TEXT,amount REAL,ts DATETIME DEFAULT CURRENT_TIMESTAMP);
""")
for _c in ("game", "item", "nick", "dx_id", "dx_fields"):
    try: db.execute(f"ALTER TABLE orders ADD COLUMN {_c} TEXT DEFAULT ''")
    except sqlite3.OperationalError: pass
try: db.execute("ALTER TABLE users ADD COLUMN lang_set INTEGER DEFAULT 0")
except sqlite3.OperationalError: pass
try: db.execute("ALTER TABLE users ADD COLUMN phone TEXT DEFAULT ''")
except sqlite3.OperationalError: pass
for _c, _t in (("text", "TEXT DEFAULT ''"), ("reply", "TEXT DEFAULT ''"), ("ts", "TEXT")):
    try: db.execute(f"ALTER TABLE ratings ADD COLUMN {_c} {_t}")
    except sqlite3.OperationalError: pass
try: db.execute("ALTER TABLE topups ADD COLUMN method TEXT DEFAULT ''")
except sqlite3.OperationalError: pass
db.execute("UPDATE topups SET status='expired' WHERE status='pending' AND (method IS NULL OR method='')")
try: db.execute("ALTER TABLE orders ADD COLUMN qty INTEGER DEFAULT 1")
except sqlite3.OperationalError: pass
def q(sql, a=()):
    with _l: return db.execute(sql, a)
def user(uid, name="", inviter=None):
    u = q("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    if not u:
        inv = q("SELECT id FROM users WHERE ref=?", (inviter,)).fetchone() if inviter else None
        inv = inv["id"] if inv and inv["id"] != uid else None
        q("INSERT INTO users(id,name,ref,invited_by) VALUES(?,?,?,?)", (uid, name, secrets.token_urlsafe(6).upper(), inv))
        u = q("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    return u
MAX_TOPUPS = 1   # javob berilmagan balans to'ldirish so'rovlari chegarasi
MAX_ORDERS = 3   # javob berilmagan buyurtmalar chegarasi
def _pending(uid, kind):
    """kind='topup' yoki 'order': mijozda javob berilmagan so'rovlar soni. Eski to'lovlar 12 soatdan keyin o'zi yopiladi."""
    db.execute("UPDATE topups SET status='expired' WHERE status='pending' AND ts < datetime('now','-12 hours')")
    if kind == "topup": return db.execute("SELECT COUNT(*) FROM topups WHERE uid=? AND status='pending'", (uid,)).fetchone()[0]
    return db.execute("SELECT COUNT(*) FROM orders WHERE uid=? AND status IN ('pending','processing')", (uid,)).fetchone()[0]
def has_pending(uid, kind="topup"):
    with _l: return _pending(uid, kind) >= (MAX_TOPUPS if kind == "topup" else MAX_ORDERS)
def buy(uid, title, pid, price, game="", item="", fields="", qty=1):
    """Atomik: -1 = tasdiqlanmagan so'rov bor, None = mablag' yetarli emas, aks holda buyurtma raqami."""
    with _l:
        db.execute("BEGIN IMMEDIATE")
        if _pending(uid, "order") >= MAX_ORDERS:
            db.execute("ROLLBACK"); return -1
        r = db.execute("UPDATE users SET balance=balance-?,spent=spent+? WHERE id=? AND balance>=?", (price, price, uid, price))
        if r.rowcount == 0:
            db.execute("ROLLBACK"); return None
        oid = db.execute("INSERT INTO orders(uid,title,pid,price,game,item,dx_fields,qty) VALUES(?,?,?,?,?,?,?,?)", (uid, title, pid, price, game, item, fields, qty)).lastrowid
        db.execute("INSERT INTO fin(uid,title,amount) VALUES(?,?,?)", (uid, title, -price))
        db.execute("COMMIT"); return oid
def add_topup(uid, amount, method):
    """Atomik: -1 = tasdiqlanmagan so'rov bor, aks holda so'rov raqami."""
    with _l:
        db.execute("BEGIN IMMEDIATE")
        if _pending(uid, "topup") >= MAX_TOPUPS:
            db.execute("ROLLBACK"); return -1
        tid = db.execute("INSERT INTO topups(uid,amount,method) VALUES(?,?,?)", (uid, amount, method)).lastrowid
        db.execute("COMMIT"); return tid
def cancel_order(oid):
    """Buyurtmani rad etadi va pulni mijozga qaytaradi (faqat 'pending' bo'lsa, ikki marta qaytarilmaydi)."""
    with _l:
        db.execute("BEGIN IMMEDIATE")
        o = db.execute("SELECT * FROM orders WHERE id=? AND status IN ('pending','processing')", (oid,)).fetchone()
        if not o:
            db.execute("ROLLBACK"); return None
        db.execute("UPDATE orders SET status='cancelled' WHERE id=?", (oid,))
        db.execute("UPDATE users SET balance=balance+?, spent=MAX(spent-?,0) WHERE id=?", (o["price"], o["price"], o["uid"]))
        db.execute("INSERT INTO fin(uid,title,amount) VALUES(?,?,?)", (o["uid"], "Refund", o["price"]))
        db.execute("COMMIT"); return o
def approve_topup(tid, pct):
    """Faqat 'pending' bo'lsa — bitta to'lov ikki marta qabul qilinmaydi."""
    with _l:
        db.execute("BEGIN IMMEDIATE")
        t = db.execute("SELECT * FROM topups WHERE id=? AND status='pending'", (tid,)).fetchone()
        if not t:
            db.execute("ROLLBACK"); return None
        db.execute("UPDATE topups SET status='done' WHERE id=?", (tid,))
        db.execute("UPDATE users SET balance=balance+? WHERE id=?", (t["amount"], t["uid"]))
        db.execute("INSERT INTO fin(uid,title,amount) VALUES(?,?,?)", (t["uid"], "Top up", t["amount"]))
        u = db.execute("SELECT * FROM users WHERE id=?", (t["uid"],)).fetchone()
        if u["invited_by"] and not u["paid"]:  # bonus faqat birinchi to'lovda
            b = round(t["amount"] * pct / 100, 2)
            db.execute("UPDATE users SET balance=balance+?,bonus=bonus+? WHERE id=?", (b, b, u["invited_by"]))
            db.execute("INSERT INTO fin(uid,title,amount) VALUES(?,?,?)", (u["invited_by"], "Referral bonus", b))
        db.execute("UPDATE users SET paid=1 WHERE id=?", (t["uid"],))
        db.execute("COMMIT"); return t

def dx_get(item_id, region):
    r = q("SELECT product_id FROM dxmap WHERE item_id=? AND region=?", (item_id, region or "")).fetchone()
    return r["product_id"] if r else None
def dx_set(item_id, region, product_id):
    q("INSERT OR REPLACE INTO dxmap(item_id,region,product_id) VALUES(?,?,?)", (item_id, region or "", product_id))
def dx_count():
    return q("SELECT COUNT(*) c FROM dxmap").fetchone()["c"]
def dx_attach(oid, dx_id):
    return q("UPDATE orders SET status='processing', dx_id=? WHERE id=? AND status='pending'", (dx_id, oid)).rowcount
def order_finish(oid):
    """'pending' yoki 'processing' bo'lsa 'done' qiladi; ikki marta bajarilmaydi."""
    return q("UPDATE orders SET status='done' WHERE id=? AND status IN ('pending','processing')", (oid,)).rowcount

def dxcat_replace(game_id, rows):
    with _l:
        db.execute("BEGIN IMMEDIATE")
        db.execute("UPDATE dxcat SET active=0 WHERE game_id=?", (game_id,))
        for r in rows:
            ex = db.execute("SELECT game_id, active FROM dxcat WHERE product_id=?", (r[0],)).fetchone()
            if ex and ex["active"] and ex["game_id"] != game_id: continue   # mahsulot boshqa o'yinga tegishli: ustidan yozmaymiz
            db.execute("INSERT OR REPLACE INTO dxcat(product_id,game_id,region,region_title,name,tab,emoji,price_usd,fields,kind,sort,qmin,qmax,active) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,1)", r)
        db.execute("COMMIT")
def dxcat_items(game_id):
    return q("SELECT * FROM dxcat WHERE game_id=? AND active=1 ORDER BY region, tab, sort, name", (game_id,)).fetchall()
def dxcat_get(product_id):
    return q("SELECT * FROM dxcat WHERE product_id=? AND active=1", (product_id,)).fetchone()
def dxcat_any(game_id, region):
    return (q("SELECT * FROM dxcat WHERE game_id=? AND region=? AND active=1 LIMIT 1", (game_id, region or "")).fetchone()
            or q("SELECT * FROM dxcat WHERE game_id=? AND active=1 LIMIT 1", (game_id,)).fetchone())
def dxcat_game_ids():
    return [r[0] for r in q("SELECT DISTINCT game_id FROM dxcat WHERE active=1").fetchall()]
def dxgame_get(game_id):
    return q("SELECT * FROM dxgames WHERE game_id=?", (game_id,)).fetchone()
def dxgame_set(game_id, cat, qq):
    q("INSERT OR REPLACE INTO dxgames(game_id,cat,q) VALUES(?,?,?)", (game_id, cat, qq))

def rhash_get(h):
    r = q("SELECT tid FROM rhash WHERE h=?", (h,)).fetchone()
    return r["tid"] if r else None
def rhash_add(h, tid):
    q("INSERT OR IGNORE INTO rhash(h,tid) VALUES(?,?)", (h, tid))

def snapshot(path):
    """Bazaning izchil nusxasini fayl sifatida saqlaydi (zaxira uchun)."""
    with _l:
        dst = sqlite3.connect(path)
        try: db.backup(dst)
        finally: dst.close()

def set_get(k, default=None):
    r = q("SELECT v FROM settings WHERE k=?", (k,)).fetchone()
    return r["v"] if r else default
def ov_all(): return q("SELECT * FROM catover").fetchall()
def cust_all(): return q("SELECT * FROM catcust ORDER BY id").fetchall()
def reg_all(): return q("SELECT * FROM catregion").fetchall()
def info_get(gid): return q("SELECT pos,txt,ver,(img IS NOT NULL) AS has FROM gameinfo WHERE game_id=? ORDER BY pos", (gid,)).fetchall()
def info_img(gid, pos):
    r = q("SELECT img,ver FROM gameinfo WHERE game_id=? AND pos=?", (gid, pos)).fetchone()
    return (r["img"], r["ver"]) if r else None
def info_set(gid, blocks):
    import time as _t
    ver = int(_t.time() * 1000)
    with _l:
        db.execute("BEGIN IMMEDIATE")
        try:
            db.execute("DELETE FROM gameinfo WHERE game_id=?", (gid,))
            for i, (txt, img) in enumerate(blocks): db.execute("INSERT INTO gameinfo(game_id,pos,img,txt,ver) VALUES(?,?,?,?,?)", (gid, i, img, txt, ver))
            db.execute("COMMIT")
        except Exception:
            db.execute("ROLLBACK"); raise
def auto_all(banned=False):
    rows = q("SELECT * FROM autogames").fetchall()
    return rows if banned else [r for r in rows if not r["banned"]]
def auto_get(gid): return q("SELECT * FROM autogames WHERE game_id=? AND banned=0", (gid,)).fetchone()
def auto_set(gid, name, cats):
    import json as _j
    q("INSERT INTO autogames(game_id,name,cats) VALUES(?,?,?) ON CONFLICT(game_id) DO UPDATE SET name=excluded.name, cats=excluded.cats", (gid, name, _j.dumps(cats)))
def auto_ban(gid):
    q("UPDATE autogames SET banned=1 WHERE game_id=?", (gid,)); q("UPDATE dxcat SET active=0 WHERE game_id=?", (gid,))
def tabmv_all(): return {r["item_id"]: r["tab"] for r in q("SELECT * FROM cattab").fetchall()}
def tabren_all(): return q("SELECT * FROM cattabname").fetchall()
def ghide_all(): return {r["game_id"] for r in q("SELECT game_id FROM gamehide").fetchall()}
def admin_apply(gid, edits, adds, dels, regions, hide_game, settings, tabren=None):
    """Admin o'zgartirishlarini bitta tranzaksiyada saqlaydi."""
    with _l:
        db.execute("BEGIN IMMEDIATE")
        try:
            for e in edits:
                iid = e["id"]
                if iid.startswith("c") and iid[1:].isdigit():
                    row = db.execute("SELECT * FROM catcust WHERE id=? AND game_id=?", (int(iid[1:]), gid)).fetchone()
                    if row:
                        price = row["price"] if e.get("reset") or "price" not in e else e["price"]
                        db.execute("UPDATE catcust SET name=?, price=?, hidden=? WHERE id=?", (e.get("name") or row["name"], price, int(e["hidden"]) if "hidden" in e else row["hidden"], row["id"]))
                        if e.get("tab"): db.execute("UPDATE catcust SET tab=? WHERE id=?", (e["tab"], row["id"]))
                else:
                    cur = db.execute("SELECT * FROM catover WHERE item_id=?", (iid,)).fetchone()
                    name = e["name"] if "name" in e else (cur["name"] if cur else None)
                    price = None if e.get("reset") else (e["price"] if "price" in e else (cur["price"] if cur else None))
                    hidden = int(e["hidden"]) if "hidden" in e else (cur["hidden"] if cur else 0)
                    if name is None and price is None and not hidden: db.execute("DELETE FROM catover WHERE item_id=?", (iid,))
                    else: db.execute("INSERT OR REPLACE INTO catover(item_id,name,price,hidden) VALUES(?,?,?,?)", (iid, name, price, hidden))
                    if e.get("tab"):   # bo'limga ko'chirish (Donatix qayta sinxronlansa ham saqlanadi)
                        if e["tab"] == e.get("tab0"): db.execute("DELETE FROM cattab WHERE item_id=?", (iid,))
                        else: db.execute("INSERT OR REPLACE INTO cattab(item_id,tab) VALUES(?,?)", (iid, e["tab"]))
            for a in adds: db.execute("INSERT INTO catcust(game_id,region,tab,name,price,sku,hidden) VALUES(?,?,?,?,?,?,?)", (gid, a["region"], a["tab"], a["name"], a["price"], a["sku"], a["hidden"]))
            for c in dels: db.execute("DELETE FROM catcust WHERE id=? AND game_id=?", (c, gid))
            for rg in regions: db.execute("INSERT OR REPLACE INTO catregion(game_id,region,title,hidden) VALUES(?,?,?,?)", (gid, rg["region"], rg["title"], rg["hidden"]))
            if hide_game is True: db.execute("INSERT OR IGNORE INTO gamehide(game_id) VALUES(?)", (gid,))
            elif hide_game is False: db.execute("DELETE FROM gamehide WHERE game_id=?", (gid,))
            for tr in (tabren or []):   # bo'lim nomini o'zgartirish
                new = tr["to"]
                for t0 in tr["origs"]:
                    if t0 == new: db.execute("DELETE FROM cattabname WHERE game_id=? AND old=?", (gid, t0))
                    else: db.execute("INSERT OR REPLACE INTO cattabname(game_id,old,new) VALUES(?,?,?)", (gid, t0, new))
                for iid in tr["ids"]:
                    db.execute("UPDATE cattab SET tab=? WHERE item_id=? AND tab=?", (new, iid, tr["from"]))
                db.execute("UPDATE catcust SET tab=? WHERE game_id=? AND tab=?", (new, gid, tr["from"]))
            for k, v in settings.items(): db.execute("INSERT OR REPLACE INTO settings(k,v) VALUES(?,?)", (k, str(v)))
            db.execute("COMMIT")
        except Exception:
            db.execute("ROLLBACK"); raise

def icon_set(gid, url): q("INSERT INTO gameicon(game_id,url) VALUES(?,?) ON CONFLICT(game_id) DO UPDATE SET url=excluded.url", (gid, url))
def icon_get(gid):
    r = q("SELECT url FROM gameicon WHERE game_id=?", (gid,)).fetchone()
    return r["url"] if r else None
