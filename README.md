# Donat bot
Render: Build `pip install -r requirements.txt`, Start `python main.py`.
Environment: BOT_TOKEN, ADMIN_ID, MINIAPP_URL (Render havolasi), CARD_NUMBER, CARD_HOLDER, SUPPORT_USERNAME

## O'yinchi ID ni tekshirish (ixtiyoriy)
Render -> Environment:
- IDCHECK_URL   = yetkazib beruvchi havolasi, masalan https://api.provider.com/check?game={game}&uid={id}&region={region}&key=KALIT
- IDCHECK_NICK  = javobdagi nik joyi (JSON yo'li), masalan data.nickname
- IDCHECK_GAMES = (ixtiyoriy) {"freefire":"ff","pubg":"pubgm"}
- IDCHECK_HEADERS = (ixtiyoriy) {"Authorization":"Bearer ..."}
Javob 404 bo'lsa ID yo'q hisoblanadi; boshqa xatoda "ID tasdiqlanmadi" ogohlantirishi chiqadi, buyurtma baribir berilishi mumkin.

## Donatix (avto yetkazib berish)
Render -> Environment:
- DONATIX_KEY = API kalit (faqat shu yerda, GitHub'ga yozmang)
- USD_TJS = 1 dollar necha somoni (tannarx tekshiruvi uchun, tavsiya etiladi)
- DX_MIN_BALANCE = Donatix balansi shundan kam bo'lsa ogohlantirish (dollarda, standart 5)
Botda (faqat admin): /dx /dxcats /dxfind matn /dxauto o'yin_id /dxset item_id REGION product_id /dxpause /dxresume
