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

## Donatix katalogi (avto)
Botda (admin): /dxsync - Donatix'dan o'yinlar va paketlarni oladi (Free Fire, PUBG, Mobile Legends, Clash of Clans, Telegram Premium/Stars),
narxga ustama qo'shadi (DX_MARKUP, standart 30%), kursi USD_TJS. Keyin har 30 daqiqada o'zi yangilanadi.
Topilmasa: /dxcats so'z, /dxcat o'yin_id kategoriya_id, so'ng /dxsync o'yin_id. Tuzatish: /dxraw yo'l (masalan glory/regions)

## Chekni AI bilan tekshirish (ixtiyoriy)
Render -> Environment: ANTHROPIC_API_KEY (Claude API kaliti), AI_MODEL (ixtiyoriy). Chek adminga kelgach, tagiga AI natijasi qo'shiladi:
chek ekanligi, summa, qabul qiluvchi raqam, sana, tahrir belgilari. Qaror baribir adminda. Bir xil chek rasmi ikki marta qabul qilinmaydi.

## Majburiy obuna
Render -> Environment: REQUIRED_CHANNELS = @kanal1,@kanal2
Yopiq kanal: -1001234567890|https://t.me/+InviteKod|Kanal nomi  (vergul bilan ajrating)
Bot HAR BIR kanalda admin bo'lishi shart. Oqim: /start -> til -> obuna -> «Tekshirish» -> menyu. Obunasiz Mini App ham ochilmaydi (API 403).

## Admin panel qulfi (PIN / Face ID / Touch ID)
Sozlash shart emas — birinchi marta admin panelga kirganda ilovaning o'zi PIN o'rnatishni so'raydi (4-8 raqam).
Telefon Face ID/Touch ID'ni qo'llab-quvvatlasa, shu PIN unga bog'lanadi va keyingi safar biometrika bilan ochish mumkin.
5 marta noto'g'ri PIN -> 5 daqiqaga qulflanadi. PIN'ni unutsangiz yoki qurilma almashsangiz, botga yuboring: /setpin 123456

## Excel eksport va statistika
Admin panel -> Statistika: bugungi/haftalik/oylik daromad, kutilayotgan buyurtma-to'lovlar, eng ko'p sotilgan o'yinlar, Excel yuklab olish tugmalari.
Fayl har doim sizning shaxsiy Telegram chatingizga yuboriladi. Har Dushanba ertalab soat 9:00 da o'tgan haftalik hisobot o'zi yuboriladi.
Qo'lda: botga /excel 7  yoki  /excel 30  yoki  /excel all


## To'lov usullari
Render -> Environment:
- DCITY_PHONE = Dushanbe City telefon raqami (yagona to'lov usuli; eski DCITY_CARD ham ishlaydi)
- DCITY_HOLDER = karta egasi ismi (ixtiyoriy, bo'lmasa CARD_HOLDER olinadi)
Logotip: dc.png faylini qo'shsangiz (1024x1024) chiqadi, bo'lmasa «DC» belgisi ko'rinadi.
