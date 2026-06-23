import logging
import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Bot tokeni va Kanal ID sini yozing
BOT_TOKEN = "8816635869:AAG5R7mv9dJS-H-LYAT7ALCY2PDp6hSEdBE"
CHANNEL_ID = "@kosonsoygullari_official"
ADMIN_ID = 644872296  # O'zingizning Telegram ID raqamingizni yozing

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)

# Bot va Dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Ma'lumotlar bazasini sozlash
conn = sqlite3.connect("bot_database.db")
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        phone TEXT,
        id_number INTEGER
    )
''')
conn.commit()

# FSM (Holatlar)
class Registration(StatesGroup):
    waiting_for_channel = State()
    waiting_for_phone = State()

class AdminStates(StatesGroup):
    waiting_for_broadcast = State()

# Klaviaturalar
def get_user_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🆔 Mening ID"), KeyboardButton(text="📢 Bizning kanal")],
            [KeyboardButton(text="📞 Aloqa"), KeyboardButton(text="❓ Yordam")]
        ],
        resize_keyboard=True
    )

def get_admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Foydalanuvchilar ro'yxati"), KeyboardButton(text="📥 Hamma ID larni yuklash")],
            [KeyboardButton(text="❌ ID larni o'chirish"), KeyboardButton(text="✉️ Xabar tarqatish")],
            [KeyboardButton(text="🏠 Foydalanuvchi menyusi")]
        ],
        resize_keyboard=True
    )

def get_check_inline():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Kanalga o'tish", url=f"https://t.me/kosonsoygullari_official")],
            [InlineKeyboardButton(text="✅ A'zo bo'ldim", callback_data="check_subs")]
        ]
    )

# --- START KOMANDASI ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if user:
        await message.answer(f"Xush kelibsiz! Siz allaqachon ro'yxatdan o'tgansiz. ID raqamingiz: {user[3]}", reply_markup=get_user_menu())
        if user_id == ADMIN_ID:
            await message.answer("Siz adminsiz. Admin panelga o'tish uchun /admin buyrug'ini yozing.")
    else:
        try:
            member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
            if member.status in ['member', 'administrator', 'creator']:
                await request_phone(message, state)
            else:
                await message.answer("Konkursda qatnashish uchun avval kanalimizga a'zo bo'ling:", reply_markup=get_check_inline())
                await state.set_state(Registration.waiting_for_channel)
        except Exception:
            await message.answer("Konkursda qatnashish uchun avval kanalimizga a'zo bo'ling:", reply_markup=get_check_inline())
            await state.set_state(Registration.waiting_for_channel)

async def request_phone(message: types.Message, state: FSMContext):
    phone_button = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("Roʻyxatdan oʻtish uchun quyidagi tugma orqali telefon raqamingizni yuboring:", reply_markup=phone_button)
    await state.set_state(Registration.waiting_for_phone)

# --- INLINE KNOPKA TEKSHIRUVI ---
@dp.callback_query(F.data == "check_subs")
async def check_subscription(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            await call.message.delete()
            await request_phone(call.message, state)
        else:
            await call.answer("Siz hali kanalga a'zo bo'lmadingiz!", show_alert=True)
    except Exception:
        await call.answer("Bot kanalni tekshira olmadi. Botni kanalda admin qiling!", show_alert=True)

# --- TELEFON RAQAM QABUL QILISH ---
@dp.message(Registration.waiting_for_phone, F.contact)
async def process_phone(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or "Mavjud emas"
    phone = message.contact.phone_number
    
    cursor.execute("SELECT MAX(id_number) FROM users")
    max_id = cursor.fetchone()[0]
    new_id = 1001 if max_id is None else max_id + 1
    
    cursor.execute(
        "INSERT INTO users (user_id, username, phone, id_number) VALUES (?, ?, ?, ?)", 
        (user_id, username, phone, new_id)
    )
    conn.commit()
    
    await state.clear()
    await message.answer(f"🎉 Tabriklaymiz! Siz muvaffaqiyatli ro'yxatdan o'tdingiz.\n\nSizning ID raqamingiz: *{new_id}*", parse_mode="Markdown", reply_markup=get_user_menu())

# --- FOYDALANUVCHI MENYUSI FUNKSIYALARI ---
@dp.message(F.text == "🆔 Mening ID")
async def show_my_id(message: types.Message):
    cursor.execute("SELECT id_number FROM users WHERE user_id = ?", (message.from_user.id,))
    res = cursor.fetchone()
    if res:
        await message.answer(f"Sizning ID raqamingiz: *{res[0]}*", parse_mode="Markdown")
    else:
        await message.answer("Siz ro'yxatdan o'tmagansiz. /start ni bosing.")

@dp.message(F.text == "📢 Bizning kanal")
async def show_channel(message: types.Message):
    await message.answer("Bizning rasmiy kanalimiz: @kosonsoygullari_official\nUlanish: https://t.me/kosonsoygullari_official")

@dp.message(F.text == "📞 Aloqa")
async def show_contact(message: types.Message):
    await message.answer("Savollar va takliflar bo'yicha admin bilan bog'laning:\n👉 +998900503362  @kosonsoygullari_admin")

@dp.message(F.text == "❓ Yordam")
async def show_help(message: types.Message):
    await message.answer("Ushbu bot 'Kosonsoy Gullari' kanali konkursida qatnashish uchun ID raqam beradi.\nHisobingiz faol bo'lishi uchun kanaldan chiqib ketmasligingiz kerak.")

# --- ADMIN PANEL ---
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Admin panelga xush kelibsiz:", reply_markup=get_admin_menu())

@dp.message(F.text == "🏠 Foydalanuvchi menyusi")
async def back_to_user(message: types.Message):
    await message.answer("Foydalanuvchi menyusiga qaytdingiz:", reply_markup=get_user_menu())

@dp.message(F.text == "👥 Foydalanuvchilar ro'yxati")
async def admin_users_count(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        await message.answer(f"Botdagi jami ishtirokchilar soni: {count} ta")

@dp.message(F.text == "📥 Hamma ID larni yuklash")
async def admin_download_ids(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        cursor.execute("SELECT id_number, phone, username FROM users")
        rows = cursor.fetchall()
        if not rows:
            return await message.answer("Hozircha hech kim ro'yxatdan o'tmagan.")
        
        text = "ID | Telefon | Username\n" + "-"*30 + "\n"
        for row in rows:
            text += f"{row[0]} | {row[1]} | @{row[2]}\n"
        
        with open("ishtirokchilar.txt", "w", encoding="utf-8") as f:
            f.write(text)
        
        document = types.FSInputFile("ishtirokchilar.txt")
        await message.answer_document(document, caption="Barcha ishtirokchilar ro'yxati")

# KUCHAYTIRILGAN O'CHIRISH VA XABAR YUBORISH TIZIMI
@dp.message(F.text == "❌ ID larni o'chirish")
async def admin_clear_ids(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()
        
        if not users:
            return await message.answer("Bazada o'chirish uchun hech qanday ishtirokchi yo'q.")
        
        notification_text = (
            "⚠️ **Diqqat, konkurs ishtirokchilari!**\n\n"
            "Navbatdagi konkursimiz yakunlandi va barcha berilgan ID raqamlar bekor qilindi.\n"
            "Yaqin kunlarda yeni konkurs start oladi! Yangi ID raqam olish uchun botni qayta faollashtirishingiz ( /start bosishingiz ) kerak bo'ladi.\n\n"
            "Bizni kuzatishda davom eting: @kosonsoygullari_official"
        )
        
        await message.answer(f"Jami {len(users)} ta ishtirokchiga ogohlantirish xabari yuborilmoqda, iltimos kuting...")
        
        send_count = 0
        for user in users:
            try:
                await bot.send_message(chat_id=user[0], text=notification_text, parse_mode="Markdown")
                send_count += 1
                await asyncio.sleep(0.05)
            except Exception:
                pass
        
        cursor.execute("DELETE FROM users")
        conn.commit()
        
        await message.answer(
            f"✅ **ID larni tozalash yakunlandi!**\n\n"
            f"📬 Xabar muvaffaqiyatli yetib bordi: {send_count} ta ishtirokchiga\n"
            f"🧹 Hamma ma'lumotlar bazadan butunlay o'chirildi.",
            reply_markup=get_admin_menu()
        )

@dp.message(F.text == "✉️ Xabar tarqatish")
async def admin_broadcast_start(message: types.Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Barcha foydalanuvchilarga yuboriladigan xabar matnini kiriting:")
        await state.set_state(AdminStates.waiting_for_broadcast)

@dp.message(AdminStates.waiting_for_broadcast)
async def admin_broadcast_send(message: types.Message, state: FSMContext):
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    await state.clear()
    
    send_count = 0
    await message.answer("Xabar yuborish boshlandi...")
    for user in users:
        try:
            await bot.send_message(chat_id=user[0], text=message.text)
            send_count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
    await message.answer(f"Xabar tarqatildi. {send_count} ta foydalanuvchiga yetib bordi.", reply_markup=get_admin_menu())

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())async def main():
    # Render tekin serverida bot o'chib qolmasligi uchun kichik port ochamiz
    import os
    from aiogram.webhook.aiohttp_impl import setup_application
    from aiohttp import web
    
    # Oddiy bo'sh aiohttp sayt ishga tushiramiz (Render buni talab qiladi)
    app = web.Application()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 8080)))
    await site.start()
    
    # Botni ishga tushirish
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())