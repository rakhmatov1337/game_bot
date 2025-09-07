import asyncio
import re
import os
import requests
import json
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command

uniname = "Free fire turnir"
# ===== CONFIG =====
API_TOKEN = "8111560279:AAErxY2923NX2407ck7erOu0jLAZ_dKXXCc"
ADMIN_ID = 7931426337          # Admin ID

# Majburiy obuna linklari
TELEGRAM_CHANNEL = "@Azamxon_Dino74"  # O'z kanalingizni qo'ying
YOUTUBE_CHANNEL = "https://youtube.com/@dino74sff?si=YrLirpaIxPPIYWWt"  # O'z YouTube kanalingizni qo'ying
INSTAGRAM_ACCOUNT = "https://www.instagram.com/dino74s?igsh=MTJ0ZWR1b20yd3R0eg%3D%3D&utm_source=qr"  # O'z Instagram akkauntingizni qo'ying

# Django API URL
DJANGO_API_URL = "http://127.0.0.1:8000/api/bot-data/"
CHANNELS_API_URL = "http://127.0.0.1:8000/api/channels/"
TEAMS_API_URL = "http://127.0.0.1:8000/api/teams/"
SOLO_PLAYERS_API_URL = "http://127.0.0.1:8000/api/solo-players/"
MY_TEAM_API_URL = "http://127.0.0.1:8000/api/my-team/"
JOIN_TEAM_API_URL = "http://127.0.0.1:8000/api/join-team/"
REMOVE_MEMBER_API_URL = "http://127.0.0.1:8000/api/remove-member/"

# Excel fayl kerak emas - faqat Django bazasiga saqlaymiz

# ===== GLOBAL VARIABLES =====
pending_referral_codes = {}  # user_id -> referral_code

# ===== STATES =====
class RegistrationForm(StatesGroup):
    # Asosiy ma'lumotlar
    fullname = State()
    birthdate = State()
    freefire_id = State()
    direction = State()
    phone = State()

class TeamManagementForm(StatesGroup):
    # Jamoa boshqaruvi
    remove_member = State()
    team_settings = State()

# ===== Asosiy menyu klaviaturasi =====
def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏆 Ro'yxatdan o'tish")],
            [KeyboardButton(text="🏆 Jamoa yaratish"), KeyboardButton(text="🔍 Jamoalar ro'yxati")],
            [KeyboardButton(text="👤 Solo o'yinchilar"), KeyboardButton(text="👥 Mening jamoam")],
            [KeyboardButton(text="ℹ️ Ma'lumot"), KeyboardButton(text="📞 Aloqa uchun")]
        ],
        resize_keyboard=True
    )


# ===== Orqaga tugmasi =====
def back_button():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )

# ===== Obuna tekshirish =====
async def check_subscription(bot: Bot, user_id: int) -> bool:
    """Telegram kanalga obuna bo'lganligini tekshirish"""
    try:
        member = await bot.get_chat_member(TELEGRAM_CHANNEL, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# ===== Django API bilan ishlash =====
async def save_to_django(data):
    """Ma'lumotlarni Django API orqali saqlash"""
    try:
        response = requests.post(DJANGO_API_URL, json=data, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Django API xatosi: {response.status_code}")
            return False
    except Exception as e:
        print(f"Django API bilan bog'lanishda xato: {e}")
        return False

async def get_channels_from_django():
    """Django dan obuna kanallarini olish"""
    try:
        response = requests.get(CHANNELS_API_URL, timeout=10)
        if response.status_code == 200:
            return response.json().get('channels', [])
        else:
            return []
    except Exception as e:
        print(f"Kanal ma'lumotlarini olishda xato: {e}")
        return []

async def check_user_registered(user_id):
    """Foydalanuvchi allaqachon ro'yxatdan o'tganligini tekshirish"""
    try:
        response = requests.get(f"{DJANGO_API_URL}check/{user_id}/", timeout=10)
        if response.status_code == 200:
            return response.json().get('registered', False)
        else:
            return False
    except Exception as e:
        print(f"Foydalanuvchi tekshirishda xato: {e}")
        return False

async def get_available_teams():
    """Mavjud jamoalar ro'yxatini olish"""
    try:
        response = requests.get(TEAMS_API_URL, timeout=10)
        if response.status_code == 200:
            return response.json().get('teams', [])
        else:
            return []
    except Exception as e:
        print(f"Jamoalar ro'yxatini olishda xato: {e}")
        return []

async def get_solo_players():
    """Solo o'yinchilar ro'yxatini olish"""
    try:
        response = requests.get(SOLO_PLAYERS_API_URL, timeout=10)
        if response.status_code == 200:
            return response.json().get('players', [])
        else:
            return []
    except Exception as e:
        print(f"Solo o'yinchilar ro'yxatini olishda xato: {e}")
        return []

async def get_my_team(user_id):
    """Foydalanuvchining jamoasini olish"""
    try:
        response = requests.get(f"{MY_TEAM_API_URL}{user_id}/", timeout=10)
        if response.status_code == 200:
            return True, response.json()
        return False, {'error': 'Jamoangizni olishda xato'}
    except Exception as e:
        print(f"Jamoangizni olishda xato: {e}")
        return False, {'error': str(e)}

async def join_team_by_code(user_id, team_code):
    """Jamoa kodiga qo'shilish"""
    try:
        data = {'user_id': user_id, 'team_code': team_code}
        response = requests.post(JOIN_TEAM_API_URL, json=data, timeout=10)
        return response.status_code == 200, response.json()
    except Exception as e:
        print(f"Jamoa kodiga qo'shilishda xato: {e}")
        return False, {'error': str(e)}

async def remove_team_member(captain_id, member_id):
    """Jamoa a'zosini chiqarish"""
    try:
        data = {'captain_id': captain_id, 'member_id': member_id}
        response = requests.post(REMOVE_MEMBER_API_URL, json=data, timeout=10)
        return response.status_code == 200, response.json()
    except Exception as e:
        print(f"A'zo chiqarishda xato: {e}")
        return False, {'error': str(e)}

async def check_user_exists(user_id):
    """Foydalanuvchi mavjudligini tekshirish"""
    try:
        response = requests.get(f"{DJANGO_API_URL}check/{user_id}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Django API 'registered' qaytaradi, 'exists' emas
            return True, {'exists': data.get('registered', False), 'data': data}
        else:
            return False, {'error': f'HTTP {response.status_code}'}
    except Exception as e:
        print(f"Foydalanuvchi tekshirishda xato: {e}")
        return False, {'error': str(e)}

# ===== Obuna tugmalari =====
def subscription_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Telegram Kanal", url=f"https://t.me/{TELEGRAM_CHANNEL[1:]}")],
            [InlineKeyboardButton(text="📺 YouTube", url=YOUTUBE_CHANNEL)],
            [InlineKeyboardButton(text="📷 Instagram", url=INSTAGRAM_ACCOUNT)],
            [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_subscription")]
        ]
    )


# ===== /start =====
async def cmd_start(message: Message, bot: Bot):
    # Obuna tekshirish
    if not await check_subscription(bot, message.from_user.id):
        await message.answer(
            f"Salom, {message.from_user.first_name}! 👋\n\n"
            f"Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
            reply_markup=subscription_keyboard()
        )
        return
    
    # Referal link orqali qo'shilish tekshirish
    if message.text and message.text.startswith('/start join_'):
        referral_code = message.text.replace('/start join_', '')
        
        # Foydalanuvchi ro'yxatdan o'tganligini tekshirish
        success, result = await check_user_exists(message.from_user.id)
        if not success or not result.get('exists', False):
            # Foydalanuvchi ro'yxatdan o'tmagan, referal kodni saqlash va to'g'ridan-to'g'ri ro'yxatdan o'tish
            pending_referral_codes[message.from_user.id] = referral_code
            await message.answer(
                f"🎮 <b>Free Fire Turnir Botiga xush kelibsiz, {message.from_user.first_name}!</b>\n\n"
                f"Jamoaga qo'shilish uchun ro'yxatdan o'ting:",
                reply_markup=main_menu(),
                parse_mode="HTML"
            )
            return
        
        # Foydalanuvchi mavjud, jamoaga qo'shilish
        success, result = await join_team_by_code(message.from_user.id, referral_code)
        
        if success:
            team_name = result.get('team_name', 'Noma\'lum')
            captain_name = result.get('captain_name', 'Noma\'lum')
            await message.answer(
                f"✅ <b>Jamoa kodiga muvaffaqiyatli qo'shildingiz!</b>\n\n"
                f"Jamoa: {team_name}\n"
                f"Sardor: {captain_name}\n\n"
                f"Endi turnir uchun tayyorlaning! 🔥",
                reply_markup=main_menu(),
                parse_mode="HTML"
            )
            return
        else:
            error_msg = result.get('error', 'Noma\'lum xato')
            await message.answer(
                f"❌ <b>Jamoa kodiga qo'shila olmadingiz!</b>\n\n"
                f"Sabab: {error_msg}",
                reply_markup=main_menu(),
                parse_mode="HTML"
            )
            return
    
    await message.answer(
        f"Salom, {message.from_user.first_name}! {uniname} botimizga xush kelibsiz 👋",
        reply_markup=main_menu()
    )

# ===== Universitet haqida =====
async def about_university(message: Message):
    info_text = """
🏆 <b>VILOYATLAR O'RTASIDA TURNIR</b> 🏆

💰 <b>Qo'yilgan summa:</b> 4000 💎
🎮 <b>O'yin tartibi:</b> Squad 4
📅 <b>Boshlanish sanasi:</b> 15 Sentabrdan

💪 <b>Omad tilaymiz!</b>
    """
    await message.answer(info_text, parse_mode="HTML")

# ===== Aloqa uchun =====
async def contact_info(message: Message):
    text = "Aloqaga chiqish uchun quyidagi havolani bosing:"
    link_btn = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👨‍💻 Aloqa uchun", url="https://telegram.me/Abdurakhim")]
        ]
    )
    await message.answer(text, reply_markup=link_btn)

# ===== Ro'yxatdan o'tish boshlanishi =====
async def registration_start(message: Message, state: FSMContext):
    # Foydalanuvchi allaqachon ro'yxatdan o'tganligini tekshirish
    if await check_user_registered(message.from_user.id):
        await message.answer(
            "❌ Siz allaqachon ro'yxatdan o'tgansiz!\n\n"
            "Agar ma'lumotlaringizni o'zgartirmoqchi bo'lsangiz, admin bilan bog'laning.",
            reply_markup=main_menu()
        )
        return
    
    await message.answer(
        "🏆 <b>Ro'yxatdan o'tish</b>\n\n"
        "Ma'lumotlaringizni to'ldiring:",
        parse_mode="HTML"
    )
    await message.answer("To'liq ismingizni yuboring:", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Orqaga")]],
        resize_keyboard=True
    ))
    await state.set_state(RegistrationForm.fullname)

# ===== Jamoa yaratish boshlanishi =====
async def create_team_start(message: Message, state: FSMContext):
    # Foydalanuvchi ro'yxatdan o'tganligini tekshirish
    success, result = await check_user_exists(message.from_user.id)
    if not success or not result.get('exists', False):
        await message.answer(
            "❌ Jamoa yaratish uchun avval ro'yxatdan o'ting!",
            reply_markup=main_menu()
        )
        return
    
    # Foydalanuvchi allaqachon jamoada ekanligini tekshirish
    success, result = await get_my_team(message.from_user.id)
    if success and result.get('team'):
        await message.answer(
            "❌ Siz allaqachon jamoadasiz!\n\n"
            "Boshqa jamoa yaratish uchun avval jamoangizdan chiqing.",
            reply_markup=main_menu()
        )
        return
    
    await message.answer(
        "🏆 <b>Jamoa yaratish</b>\n\n"
        "Jamoa nomini yuboring:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 Orqaga")]],
            resize_keyboard=True
        ),
        parse_mode="HTML"
    )
    await state.set_state(TeamManagementForm.team_settings)

async def process_team_name(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("Asosiy menyu:", reply_markup=main_menu())
        return
    
    team_name = message.text
    
    # Django API ga jamoa yaratish so'rovi
    django_data = {
        'user_id': message.from_user.id,
        'team_name': team_name,
        'action': 'create_team'
    }
    
    django_result = await save_to_django(django_data)
    
    if django_result and django_result.get('success', False):
        referral_code = django_result.get('referral_code', '')
        referral_link = f"https://t.me/Free_Fire_turnirbot?start=join_{referral_code}"
        
        success_message = (
            f"✅ <b>Jamoa muvaffaqiyatli yaratildi!</b>\n\n"
            f"🏆 Jamoa nomi: {team_name}\n"
            f"👑 Siz jamoa sardorisiz\n\n"
            f"🔗 <b>Referal link:</b>\n{referral_link}\n\n"
            f"Bu linkni boshqalarga yuboring va ular sizning jamoangizga qo'shiladi!"
        )
    else:
        success_message = "❌ Jamoa yaratishda xato yuz berdi. Qaytadan urinib ko'ring."
    
    await message.answer(success_message, reply_markup=main_menu(), parse_mode="HTML")
    await state.clear()



async def process_fullname(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("Asosiy menyu:", reply_markup=main_menu())
        return
    await state.update_data(fullname=message.text)
    await message.answer("Tug‘ilgan sanangizni kiriting (kk.oo.yyyy formatda):", reply_markup=back_button())
    await state.set_state(RegistrationForm.birthdate)

async def process_birthdate(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("Asosiy menyu:", reply_markup=main_menu())
        return
    if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', message.text):
        await message.answer("⚠️ Format noto‘g‘ri! kk.oo.yyyy formatda kiriting.")
        return
    await state.update_data(birthdate=message.text)

    await message.answer("Free Fire dagi ID raqamingizni kiriting:", reply_markup=back_button())
    await state.set_state(RegistrationForm.freefire_id)

async def process_freefire_id(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("Asosiy menyu:", reply_markup=main_menu())
        return

    await state.update_data(freefire_id=message.text)

    directions = [
        "Andijon", "Farg'ona", "Namangan", "Toshkent",
        "Sirdaryo", "Jizzax", "Samarqand", "Qashqadaryo",
        "Surxondaryo", "Navoiy", "Buxoro", "Xorazm"
    ]

    row_width = 2
    keyboard_layout = [directions[i:i + row_width] for i in range(0, len(directions), row_width)]

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btn) for btn in row] for row in keyboard_layout] + [[KeyboardButton(text="🔙 Orqaga")]],
        resize_keyboard=True
    )

    await message.answer("Viloyatingizni tanlang:", reply_markup=kb)
    await state.set_state(RegistrationForm.direction)

async def process_direction(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("Asosiy menyu:", reply_markup=main_menu())
        return
    await state.update_data(direction=message.text)
    
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )
    await message.answer("Telefon raqamingizni yuboring yoki yozing:", reply_markup=kb)
    await state.set_state(RegistrationForm.phone)


async def process_phone(message: Message, state: FSMContext, bot: Bot):
    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("Asosiy menyu:", reply_markup=main_menu())
        return

    if message.contact:
        phone_number = message.contact.phone_number
    else:
        phone_number = message.text

    await state.update_data(phone=phone_number)
    data = await state.get_data()

    # Django API ga yuborish - to'g'ridan-to'g'ri solo ro'yxatdan o'tish
    django_data = {
        'fullname': data['fullname'],
        'birthdate': data['birthdate'],
        'direction': data['direction'],
        'phone': phone_number,
        'freefire_id': data['freefire_id'],
        'user_id': message.from_user.id,
        'username': message.from_user.username if message.from_user.username else "",
        'registration_type': 'solo'  # Har doim solo bilan boshlaydi
    }
    
    # Agar referal kod bo'lsa, team_player status bilan ro'yxatdan o'tish
    if message.from_user.id in pending_referral_codes:
        django_data['registration_type'] = 'team'  # team_player status uchun
    
    django_result = await save_to_django(django_data)

    if django_result and django_result.get('success', False):
        # Agar foydalanuvchida pending referal kod bo'lsa, jamoaga qo'shilish
        if message.from_user.id in pending_referral_codes:
            referral_code = pending_referral_codes[message.from_user.id]
            del pending_referral_codes[message.from_user.id]  # O'chirish
            
            # Kichik kutish - Django bazaga saqlanish uchun
            import asyncio
            await asyncio.sleep(1)
            
            # Jamoaga qo'shilish
            success, result = await join_team_by_code(message.from_user.id, referral_code)
            if success:
                team_name = result.get('team_name', 'Noma\'lum')
                captain_name = result.get('captain_name', 'Noma\'lum')
                success_message = (
                    f"✅ <b>Ro'yxatdan o'tdingiz va jamoaga qo'shildingiz!</b>\n\n"
                    f"🏆 Jamoa: {team_name}\n"
                    f"👑 Sardor: {captain_name}\n\n"
                    f"Endi turnir uchun tayyorlaning! 🔥"
                )
            else:
                error_msg = result.get('error', 'Noma\'lum xato')
                success_message = (
                    f"✅ <b>Ro'yxatdan o'tdingiz!</b>\n\n"
                    f"❌ Jamoaga qo'shila olmadingiz: {error_msg}"
                )
        else:
            success_message = "✅ Ma'lumotlaringiz qabul qilindi! Rahmat."
    else:
        success_message = "❌ Ma'lumotlaringizni saqlashda xato yuz berdi. Qaytadan urinib ko'ring."

    await message.answer(success_message, reply_markup=main_menu(), parse_mode="HTML")
    await state.clear()

# ===== Jamoalar ro'yxati =====
async def show_teams_list(message: Message):
    teams = await get_available_teams()
    
    if not teams:
        await message.answer("❌ Hozircha mavjud jamoalar yo'q.")
        return
    
    text = "🏆 <b>Mavjud jamoalar ro'yxati:</b>\n\n"
    
    for team in teams:
        team_name = team.get('name', 'Noma\'lum')
        captain_name = team.get('captain_name', 'Noma\'lum')
        current_members = team.get('current_members', 0)
        max_members = team.get('max_members', 4)
        direction = team.get('direction', 'Noma\'lum')
        captain_username = team.get('captain_username', 'username yo\'q')
        
        text += (
            f"🏆 <b>{team_name}</b>\n"
            f"👑 Sardor: {captain_name}\n"
            f"👥 A'zolar: {current_members}/{max_members}\n"
            f"📍 Viloyat: {direction}\n"
            f"🔗 @{captain_username}\n\n"
        )
    
    await message.answer(text, parse_mode="HTML")

# ===== Solo o'yinchilar ro'yxati =====
async def show_solo_players(message: Message):
    players = await get_solo_players()
    
    if not players:
        await message.answer("❌ Hozircha solo o'yinchilar yo'q.")
        return
    
    text = "👤 <b>Solo o'yinchilar ro'yxati:</b>\n\n"
    
    for player in players:
        fullname = player.get('fullname', 'Noma\'lum')
        freefire_id = player.get('freefire_id', 'Noma\'lum')
        direction = player.get('direction', 'Noma\'lum')
        username = player.get('username', 'username yo\'q')
        status = player.get('status', 'Noma\'lum')
        
        text += (
            f"👤 <b>{fullname}</b>\n"
            f"🎮 Free Fire ID: {freefire_id}\n"
            f"📍 Viloyat: {direction}\n"
            f"📊 Status: {status}\n"
            f"🔗 @{username}\n\n"
        )
    
    await message.answer(text, parse_mode="HTML")

# ===== Mening jamoam =====
async def show_my_team(message: Message):
    success, result = await get_my_team(message.from_user.id)
    
    if success:
        team_data = result.get('team', {})
        
        team_name = team_data.get('name', 'Noma\'lum')
        captain_name = team_data.get('captain_name', 'Noma\'lum')
        current_members = team_data.get('current_members', 0)
        max_members = team_data.get('max_members', 4)
        referral_code = team_data.get('referral_code', 'Noma\'lum')
        
        referral_link = f"https://t.me/Free_Fire_turnirbot?start=join_{referral_code}"
        
        text = (
            f"🏆 <b>Mening jamoam:</b>\n\n"
            f"📛 Jamoa nomi: {team_name}\n"
            f"👑 Sardor: {captain_name}\n"
            f"👥 A'zolar: {current_members}/{max_members}\n"
            f"🔗 Referal link: <code>{referral_link}</code>\n\n"
            f"<b>Jamoa a'zolari:</b>\n"
        )
        
        for member in team_data.get('members', []):
            role = "👑" if member.get('is_captain', False) else "👤"
            username = member.get('username', 'username yo\'q')
            fullname = member.get('fullname', 'Noma\'lum')
            text += f"{role} {fullname} (@{username})\n"
        
        # Agar sardor bo'lsa, boshqarish tugmalari
        if team_data.get('is_captain', False):
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="👥 A'zo qo'shish", callback_data="add_member")],
                    [InlineKeyboardButton(text="❌ A'zo chiqarish", callback_data="remove_member")],
                    [InlineKeyboardButton(text="🔗 Referal link", callback_data="get_referral_link")]
                ]
            )
            await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await message.answer(text, parse_mode="HTML")
    else:
        error_msg = result.get('error', 'Noma\'lum xato')
        await message.answer(f"❌ Siz hali hech qanday jamoaga qo'shilmagansiz.\n\nSabab: {error_msg}")

# ===== Callback query handler =====
async def handle_callback(callback: CallbackQuery, bot: Bot):
    if callback.data == "check_subscription":
        if await check_subscription(bot, callback.from_user.id):
            await callback.message.edit_text(
                f"✅ Rahmat! Siz barcha kanallarga obuna bo'lgansiz.\n\n"
                f"Endi botdan to'liq foydalanishingiz mumkin!"
            )
            await callback.message.answer(
                "Asosiy menyu:",
                reply_markup=main_menu()
            )
        else:
            await callback.answer("❌ Hali ham barcha kanallarga obuna bo'lmagansiz!", show_alert=True)
    
    elif callback.data == "get_referral_link":
        # Foydalanuvchining jamoasini olish
        success, result = await get_my_team(callback.from_user.id)
        if success:
            team_data = result.get('team', {})
            referral_code = team_data.get('referral_code', 'Noma\'lum')
            referral_link = f"https://t.me/Free_Fire_turnirbot?start=join_{referral_code}"
            
            await callback.message.edit_text(
                f"🔗 <b>Referal link:</b>\n\n"
                f"<code>{referral_link}</code>\n\n"
                f"Bu linkni boshqalarga yuboring va ular sizning jamoangizga qo'shiladi!",
                parse_mode="HTML"
            )
        else:
            await callback.answer("❌ Jamoangizni topa olmadim!", show_alert=True)
    
    elif callback.data == "add_member":
        await callback.answer("ℹ️ Boshqa o'yinchilar referal link orqali jamoangizga qo'shiladi!", show_alert=True)
    
    elif callback.data == "remove_member":
        # Foydalanuvchining jamoasini olish
        success, result = await get_my_team(callback.from_user.id)
        if success:
            team_data = result.get('team', {})
            if team_data.get('is_captain', False):
                members = team_data.get('members', [])
                if len(members) > 1:  # Sardordan tashqari a'zolar bor
                    # A'zolar ro'yxatini ko'rsatish
                    keyboard_buttons = []
                    for member in members:
                        if not member.get('is_captain', False):  # Sardor emas
                            member_name = member.get('fullname', 'Noma\'lum')
                            button_text = f"❌ {member_name}"
                            callback_data = f"remove_{member.get('id', 0)}"
                            keyboard_buttons.append([InlineKeyboardButton(text=button_text, callback_data=callback_data)])
                    
                    if keyboard_buttons:
                        keyboard_buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_team")])
                        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
                        
                        await callback.message.edit_text(
                            "❌ <b>A'zo chiqarish</b>\n\n"
                            "Chiqarib yubormoqchi bo'lgan a'zoni tanlang:",
                            reply_markup=keyboard,
                            parse_mode="HTML"
                        )
                    else:
                        await callback.answer("ℹ️ Chiqarib yuborish uchun a'zo yo'q!", show_alert=True)
                else:
                    await callback.answer("ℹ️ Jamoada faqat siz borsiz!", show_alert=True)
            else:
                await callback.answer("ℹ️ Siz jamoa sardori emassiz!", show_alert=True)
        else:
            await callback.answer("❌ Jamoangizni topa olmadim!", show_alert=True)
    
    elif callback.data.startswith("remove_"):
        member_id = callback.data.replace("remove_", "")
        success, result = await remove_team_member(callback.from_user.id, member_id)
        
        if success:
            member_name = result.get('member_name', 'A\'zo')
            await callback.message.edit_text(
                f"✅ <b>{member_name} jamoadan chiqarildi!</b>\n\n"
                f"Endi u solo o'yinchi sifatida ro'yxatda.",
                parse_mode="HTML"
            )
        else:
            error_msg = result.get('error', 'Noma\'lum xato')
            await callback.answer(f"❌ Xato: {error_msg}", show_alert=True)
    
    elif callback.data == "back_to_team":
        # Jamoaga qaytish
        success, result = await get_my_team(callback.from_user.id)
        if success:
            team_data = result.get('team', {})
            
            team_name = team_data.get('name', 'Noma\'lum')
            captain_name = team_data.get('captain_name', 'Noma\'lum')
            current_members = team_data.get('current_members', 0)
            max_members = team_data.get('max_members', 4)
            referral_code = team_data.get('referral_code', 'Noma\'lum')
            
            referral_link = f"https://t.me/Free_Fire_turnirbot?start=join_{referral_code}"
            
            text = (
                f"🏆 <b>Mening jamoam:</b>\n\n"
                f"📛 Jamoa nomi: {team_name}\n"
                f"👑 Sardor: {captain_name}\n"
                f"👥 A'zolar: {current_members}/{max_members}\n"
                f"🔗 Referal link: <code>{referral_link}</code>\n\n"
                f"<b>Jamoa a'zolari:</b>\n"
            )
            
            for member in team_data.get('members', []):
                role = "👑" if member.get('is_captain', False) else "👤"
                username = member.get('username', 'username yo\'q')
                fullname = member.get('fullname', 'Noma\'lum')
                text += f"{role} {fullname} (@{username})\n"
            
            # Agar sardor bo'lsa, boshqarish tugmalari
            if team_data.get('is_captain', False):
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="👥 A'zo qo'shish", callback_data="add_member")],
                        [InlineKeyboardButton(text="❌ A'zo chiqarish", callback_data="remove_member")],
                        [InlineKeyboardButton(text="🔗 Referal link", callback_data="get_referral_link")]
                    ]
                )
                await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
            else:
                await callback.message.edit_text(text, parse_mode="HTML")

# ===== MAIN =====
async def main():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.register(cmd_start, Command("start"))
    dp.message.register(about_university, F.text == "ℹ️ Ma'lumot")
    dp.message.register(contact_info, F.text == "📞 Aloqa uchun")
    dp.message.register(registration_start, F.text == "🏆 Ro'yxatdan o'tish")
    dp.message.register(create_team_start, F.text == "🏆 Jamoa yaratish")
    dp.message.register(show_teams_list, F.text == "🔍 Jamoalar ro'yxati")
    dp.message.register(show_solo_players, F.text == "👤 Solo o'yinchilar")
    dp.message.register(show_my_team, F.text == "👥 Mening jamoam")
    
    # Registration form handlers
    dp.message.register(process_fullname, RegistrationForm.fullname)
    dp.message.register(process_birthdate, RegistrationForm.birthdate)
    dp.message.register(process_freefire_id, RegistrationForm.freefire_id)
    dp.message.register(process_direction, RegistrationForm.direction)
    dp.message.register(process_phone, RegistrationForm.phone)
    
    # Team management handlers
    dp.message.register(process_team_name, TeamManagementForm.team_settings)
    
    dp.callback_query.register(handle_callback)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
