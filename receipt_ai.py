"""Chek rasmini AI orqali tekshirish (ixtiyoriy). Render'da ANTHROPIC_API_KEY kerak."""
import asyncio, base64, json, logging, re, urllib.request, urllib.error
import config as C

def enabled(): return bool(C.GEMINI_KEY or C.ANTHROPIC_KEY)

PROMPT = ("You verify payment receipt screenshots for a game top-up shop in Tajikistan (banking apps such as Alif, DC Next / Dushanbe City, Korti Milli). "
          "Look ONLY at the image. Reply with ONE JSON object and nothing else:\n"
          '{"is_receipt": boolean, "status": "success"|"failed"|"unknown", "amount": number or null, "currency": string or null, '
          '"date": "YYYY-MM-DD HH:MM" or null, "recipient": string or null, "sender": string or null, '
          '"tamper_signs": [short strings such as inconsistent fonts or digits, impossible date, edited areas], "note": short string}\n'
          "Set is_receipt=false if the image is not a bank transfer confirmation (a photo of a book, a random picture, a chat screenshot).")

def _post(body):
    req = urllib.request.Request(C.AI_URL, data=json.dumps(body).encode(), method="POST",
                                 headers={"x-api-key": C.ANTHROPIC_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as r: return json.loads(r.read().decode("utf-8", "replace"))

def _gem_call(raw, media, gen, timeout):
    body = {"contents": [{"parts": [{"text": PROMPT}, {"inline_data": {"mime_type": media, "data": base64.b64encode(raw).decode()}}]}],
            "generationConfig": gen}
    req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{C.GEMINI_MODEL}:generateContent",
                                 data=json.dumps(body).encode(), method="POST",
                                 headers={"x-goog-api-key": C.GEMINI_KEY, "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read().decode("utf-8", "replace"))

def _post_gemini(raw, media):
    """1-urinish: 'o'ylash' o'chirilgan (tez). 2-urinish: oddiy sozlama (timeout yoki 400 bo'lsa). Xato sababi logga yoziladi."""
    base = {"temperature": 0, "responseMimeType": "application/json"}
    last = None
    for gen in (dict(base, thinkingConfig={"thinkingBudget": 0}), base):
        try: return _gem_call(raw, media, gen, 30)
        except urllib.error.HTTPError as e:
            logging.error("gemini HTTP %s: %s", e.code, e.read().decode("utf-8", "replace")[:400]); last = e
            if e.code != 400: break   # 400 = sozlama qo'llab-quvvatlanmadi, 2-urinishga o'tamiz; boshqa xato (403/404/429) takrorlanmaydi
        except Exception as e:
            logging.error("gemini error: %r", e); last = e
    raise last

async def analyze(raw, media="image/jpeg"):
    """dict yoki None (xato bo'lsa). Chekni o'qiydi, lekin qaror qabul qilmaydi."""
    if not enabled(): return None
    if C.GEMINI_KEY:   # Gemini (bepul) ustuvor; yo'q bo'lsa Claude
        try:
            data = await asyncio.to_thread(_post_gemini, raw, media)
            text = "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
            m = re.search(r"\{.*\}", text, re.S)
            return json.loads(m.group()) if m else None
        except Exception:
            logging.exception("receipt ai (gemini) failed"); return None
    body = {"model": C.AI_MODEL, "max_tokens": 500, "messages": [{"role": "user", "content": [
        {"type": "image", "source": {"type": "base64", "media_type": media, "data": base64.b64encode(raw).decode()}},
        {"type": "text", "text": PROMPT}]}]}
    try:
        data = await asyncio.to_thread(_post, body)
        text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        m = re.search(r"\{.*\}", text, re.S)
        return json.loads(m.group()) if m else None
    except Exception:
        logging.exception("receipt ai failed"); return None
