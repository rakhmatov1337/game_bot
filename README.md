# Game Bot - Free Fire Turnir Boti

Bu loyiha Free Fire o'yinchilari uchun turnir boti va Django admin panelini o'z ichiga oladi.

## Xususiyatlari

### Bot Xususiyatlari:
- ✅ 3 ta majburiy obuna (Telegram kanal, YouTube, Instagram)
- ✅ Telegram kanal obunasini avtomatik tekshirish
- ✅ Solo va Jamoa ro'yxatdan o'tish
- ✅ Jamoa yaratish va referal link tizimi
- ✅ Jamoa boshqaruvi (a'zo qo'shish/chiqarish)
- ✅ Mavjud jamoalar va solo o'yinchilar ro'yxati
- ✅ Django API bilan integratsiya

### Django Admin Panel:
- 📊 O'yinchilar va jamoalar ma'lumotlarini ko'rish
- 🔍 Qidiruv va filtrlash
- 📈 Statistika
- ⚙️ Obuna kanallarini boshqarish
- 👥 Jamoa boshqaruvi

## O'rnatish

### 1. Kerakli paketlarni o'rnatish:
```bash
pip install -r requirements.txt
```

### 2. Django ma'lumotlar bazasini sozlash:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Superuser yaratish:
```bash
python manage.py createsuperuser
```

### 4. Bot konfiguratsiyasi:
`freefire.py` faylida quyidagi o'zgaruvchilarni o'zgartiring:
- `API_TOKEN` - Bot token
- `ADMIN_ID` - Admin Telegram ID
- `TELEGRAM_CHANNEL` - Telegram kanal username
- `YOUTUBE_CHANNEL` - YouTube kanal linki
- `INSTAGRAM_ACCOUNT` - Instagram akkaunt linki

### 5. Ishga tushirish:

#### Django serverni ishga tushirish:
```bash
python manage.py runserver
```

#### Botni ishga tushirish:
```bash
python freefire.py
```

## Foydalanish

### Bot:
1. `/start` - Botni ishga tushirish
2. Obuna kanallariga a'zo bo'lish
3. "Ro'yxatdan o'tish" tugmasini bosish
4. Solo yoki Jamoa turini tanlash
5. Ma'lumotlarni to'ldirish
6. Jamoa yaratgan bo'lsa, referal link olish
7. Referal link orqali boshqalar jamoaga qo'shiladi

### Django Admin:
1. `http://46.101.107.199/admin/` ga o'tish
2. Superuser bilan kirish
3. Bot foydalanuvchilarini ko'rish va boshqarish

## API Endpoints

- `POST /api/bot-data/` - Bot ma'lumotlarini saqlash
- `GET /api/bot-data/check/{user_id}/` - Foydalanuvchi tekshirish
- `GET /api/teams/` - Mavjud jamoalar ro'yxati
- `GET /api/solo-players/` - Solo o'yinchilar ro'yxati
- `GET /api/my-team/{user_id}/` - Foydalanuvchi jamoasi
- `POST /api/join-team/` - Jamoa kodiga qo'shilish
- `GET /api/channels/` - Obuna kanallarini olish

## Fayl tuzilishi

```
game_bot/
├── freefire.py              # Asosiy bot kodi
├── data.xlsx               # Excel backup fayl
├── manage.py               # Django manage fayl
├── requirements.txt        # Kerakli paketlar
├── game_bot_admin/         # Django loyiha
│   ├── settings.py
│   ├── urls.py
│   └── ...
└── bot_data/               # Django app
    ├── models.py           # Ma'lumotlar bazasi modellari (Player, Team, SoloPlayer)
    ├── admin.py            # Admin panel sozlamalari
    ├── views.py            # API viewlar
    └── urls.py             # URL konfiguratsiyasi
```

## DigitalOcean Deployment

### Avtomatik deployment:
```bash
# Server ga ulanish
ssh root@46.101.107.199

# Repository ni klonlash
git clone https://github.com/rakhmatov1337/game_bot.git
cd game_bot

# Deployment script ni ishga tushirish
chmod +x deploy.sh
./deploy.sh
```

### Manual deployment:
```bash
# Docker Compose bilan
docker-compose up -d

# Yoki alohida
python manage.py runserver 0.0.0.0:8000
```

### Production URL:
- **Django Admin**: http://46.101.107.199/admin/
- **API Base**: http://46.101.107.199/api/

## Eslatmalar

- Bot ishlashi uchun Django server ishga tushirilgan bo'lishi kerak
- Telegram kanal obunasini tekshirish uchun bot kanalda admin bo'lishi kerak
- Ma'lumotlar Django bazasiga saqlanadi
- Har bir jamoa maksimal 4 ta a'zoga ega bo'lishi mumkin
- Jamoa sardori a'zolarni chiqarib yuborishi mumkin
- Referal link orqali boshqalar jamoaga qo'shiladi
- Bot username: @Free_Fire_turnirbot
- Production server: 46.101.107.199
