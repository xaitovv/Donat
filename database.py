import sqlite3, secrets, threading
_l = threading.Lock()
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
CREATE TABLE IF NOT EXISTS fin(id INTEGER PRIMARY KEY AUTOINCREMENT,uid INTEGER,title TEXT,amount REAL,ts DATETIME DEFAULT CURRENT_TIMESTAMP);
""")
for _c in ("game", "item"):
    try: db.execute(f"ALTER TABLE orders ADD COLUMN {_c} TEXT DEFAULT ''")
    except sqlite3.OperationalError: pass
try: db.execute("ALTER TABLE users ADD COLUMN lang_set INTEGER DEFAULT 0")
except sqlite3.OperationalError: pass
for _c, _t in (("text", "TEXT DEFAULT ''"), ("reply", "TEXT DEFAULT ''"), ("ts", "TEXT")):
    try: db.execute(f"ALTER TABLE ratings ADD COLUMN {_c} {_t}")
    except sqlite3.OperationalError: pass
try: db.execute("ALTER TABLE topups ADD COLUMN method TEXT DEFAULT ''")
except sqlite3.OperationalError: pass
db.execute("UPDATE topups SET status='expired' WHERE status='pending' AND (method IS NULL OR method='')")
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
def _pending(uid):
    """Mijozda tasdiqlanmagan so'rov (buyurtma yoki to'lov) bormi. Eski to'lovlar 12 soatdan keyin o'zi yopiladi."""
    db.execute("UPDATE topups SET status='expired' WHERE status='pending' AND ts < datetime('now','-12 hours')")
    return db.execute("SELECT (SELECT COUNT(*) FROM orders WHERE uid=? AND status='pending')+(SELECT COUNT(*) FROM topups WHERE uid=? AND status='pending')", (uid, uid)).fetchone()[0] > 0
def has_pending(uid):
    with _l: return _pending(uid)
def buy(uid, title, pid, price, game="", item=""):
    """Atomik: -1 = tasdiqlanmagan so'rov bor, None = mablag' yetarli emas, aks holda buyurtma raqami."""
    with _l:
        db.execute("BEGIN IMMEDIATE")
        if _pending(uid):
            db.execute("ROLLBACK"); return -1
        r = db.execute("UPDATE users SET balance=balance-?,spent=spent+? WHERE id=? AND balance>=?", (price, price, uid, price))
        if r.rowcount == 0:
            db.execute("ROLLBACK"); return None
        oid = db.execute("INSERT INTO orders(uid,title,pid,price,game,item) VALUES(?,?,?,?,?,?)", (uid, title, pid, price, game, item)).lastrowid
        db.execute("INSERT INTO fin(uid,title,amount) VALUES(?,?,?)", (uid, title, -price))
        db.execute("COMMIT"); return oid
def add_topup(uid, amount, method):
    """Atomik: -1 = tasdiqlanmagan so'rov bor, aks holda so'rov raqami."""
    with _l:
        db.execute("BEGIN IMMEDIATE")
        if _pending(uid):
            db.execute("ROLLBACK"); return -1
        tid = db.execute("INSERT INTO topups(uid,amount,method) VALUES(?,?,?)", (uid, amount, method)).lastrowid
        db.execute("COMMIT"); return tid
def cancel_order(oid):
    """Buyurtmani rad etadi va pulni mijozga qaytaradi (faqat 'pending' bo'lsa, ikki marta qaytarilmaydi)."""
    with _l:
        db.execute("BEGIN IMMEDIATE")
        o = db.execute("SELECT * FROM orders WHERE id=? AND status='pending'", (oid,)).fetchone()
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
