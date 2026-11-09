"""Render bepul rejasida fayllar har deploy va uyquda tozalanadi. Shuning uchun baza nusxasi admin chatida (qadalgan xabar sifatida)
saqlanadi va server yangidan ishga tushganda shu yerdan tiklanadi."""
import json, os, sqlite3, urllib.request
import config as C

API = "https://api.telegram.org"

def _call(method, params):
    req = urllib.request.Request(f"{API}/bot{C.BOT_TOKEN}/{method}", data=json.dumps(params).encode(),
                                 headers={"content-type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r: return json.loads(r.read().decode())

def restore(path):
    """Baza fayli yo'q bo'lsa (yangi deploy), qadalgan zaxiradan tiklaydi. Qaytaradi: log uchun matn."""
    try:
        if os.path.exists(path) and os.path.getsize(path) > 4096: return "baza fayli bor, tiklash kerak emas"
        if not (C.BOT_TOKEN and C.ADMIN_ID): return "BOT_TOKEN/ADMIN_ID yo'q"
        pm = ((_call("getChat", {"chat_id": C.ADMIN_ID}).get("result") or {}).get("pinned_message")) or {}
        doc = pm.get("document") or {}
        if not str(doc.get("file_name", "")).startswith("diavex-backup"): return "zaxira topilmadi (hali yaratilmagan)"
        fp = _call("getFile", {"file_id": doc["file_id"]})["result"]["file_path"]
        with urllib.request.urlopen(f"{API}/file/bot{C.BOT_TOKEN}/{fp}", timeout=60) as r: data = r.read()
        tmp = path + ".restore"
        with open(tmp, "wb") as f: f.write(data)
        c = sqlite3.connect(tmp)
        try: ok = c.execute("PRAGMA quick_check").fetchone()[0] == "ok"
        finally: c.close()
        if not ok or not data.startswith(b"SQLite format 3"):
            os.remove(tmp); return "zaxira buzilgan, tiklanmadi"
        os.replace(tmp, path)
        return f"TIKLANDI ({len(data) // 1024} KB)"
    except Exception as e:
        return f"tiklab bo'lmadi: {e!r}"
