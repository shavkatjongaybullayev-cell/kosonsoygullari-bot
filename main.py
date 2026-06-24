import os
import logging
import asyncio
import sqlite3
import threading
import random  # <-- AYNAN SHUNI QO'SHING
from http.server import SimpleHTTPRequestHandler, HTTPServer
import os
import logging
import asyncio
import sqlite3
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# ============================================================
# 1. ASOSIY SOZLAMALAR (Ma'lumotlar o'z joyida turibdi)
# ============================================================
BOT_TOKEN = "8816635869:AAFhYWs9TeqRp9TeYTgJdBO555h_eCXEAsc"
CHANNEL_ID = "@kosonsoygullari_official"
ADMIN_ID = 644872296  # Sizning Telegram ID raqamingiz

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

# ============================================================
# 2. FSM (HOLATLAR TIZIMI)
# ============================================================
class Registration(StatesGroup):
    waiting_for_channel = State()
    waiting_for_phone = State()

class AdminStates(StatesGroup):
    waiting_for_broadcast = State()

# ============================================================
# 3. KLAVIATURALAR (BUTTONS)
# ============================================================
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

def get_admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Foydalanuvchilar ro'yxati"), KeyboardButton(text="📥 Hamma ID larni yuklash")],
            [KeyboardButton(text="🎲 G'olibni aniqlash"), KeyboardButton(text="❌ ID larni o'chirish")], # <-- Tugma shu yerga qo'shildi
            [KeyboardButton(text="✉️ Xabar tarqatish"), KeyboardButton(text="🏠 Foydalanuvchi menyusi")]
        ],
        resize_keyboard=True
    )

# ============================================================
# 4. START KOMANDASI VA RO'YXATDAN O'TISH
# ============================================================
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

# ============================================================
# 5. FOYDALANUVCHI MENYUSI FUNKSIYALARI
# ============================================================
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

# ============================================================
# 6. ADMIN PANEL STRUKTURASI
# ============================================================
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

@dp.message(F.text == "❌ ID larni o'chirish")
async def admin_clear_ids(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        # Bazadan barcha foydalanuvchilarning ID raqamlarini olamiz
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()
        
        if not users:
            return await message.answer("Bazada o'chirish uchun hech qanday ishtirokchi yo'q.")
        
        notification_text = (
            "⚠️ **Diqqat, konkurs ishtirokchilari!**\n\n"
            "Navbatdagi konkursimiz yakunlandi va barcha berilgan ID raqamlar bekor qilindi.\n"
            "Yaqin kunlarda yangi konkurs start oladi! Yangi ID raqam olish uchun botni qayta faollashtirishingiz ( /start bosishingiz ) kerak bo'ladi.\n\n"
            "Bizni kuzatishda davom eting: @kosonsoygullari_official"
        )
        
        await message.answer(f"Jami {len(users)} ta ishtirokchiga ogohlantirish xabari yuborilmoqda, iltimos kuting...")
        
        send_count = 0
        for user in users:
            try:
                # user[0] qilib yozish shart, chunki tuple ichidan aniq ID raqamni ajratib olish kerak
                await bot.send_message(chat_id=user[0], text=notification_text, parse_mode="Markdown")
                send_count += 1
                # Telegram serveri bloklab qo'ymasligi uchun har xabardan keyin 0.05 soniya kutamiz
                await asyncio.sleep(0.05)
            except Exception as e:
                logging.error(f"Xabar yuborilmadi {user[0]}: {e}")
                pass
        
        # Xabarlar hamma ketgandan KEYIN bazani tozalaymiz
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

@dp.message(F.text == "🎲 G'olibni aniqlash")
async def admin_pick_winner(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        # Ma'lumotlarni aniq tartibda bazadan olamiz
        cursor.execute("SELECT user_id, id_number, phone, username FROM users")
        users = cursor.fetchall()
        
        if not users:
            return await message.answer("Bazada ishtirokchilar yo'q. G'olibni aniqlab bo'lmaydi.")
        
        # Ishtirokchilar soniga qarab g'oliblar sonini belgilaymiz (maksimal 4 ta)
        winners_count = min(len(users), 4)
        
        # Tasodifiy g'oliblarni tanlaymiz
        winners = random.sample(users, k=winners_count)
        
        admin_report = f"🎲 **RANDOM NATIJALARI ({winners_count} TA G'OLIB)** 🎲\n\n"
        
        for index, winner in enumerate(winners, start=1):
            # Indekslarni aniq o'z joyiga joylashtiramiz:
            winner_user_id = winner[0]   # user_id
            winner_id_number = winner[1]  # id_number
            winner_phone = winner[2]      # phone
            winner_username = winner[3]   # username
            
            # Username mavjudligini tekshiramiz
            user_link = f"@{winner_username}" if winner_username and winner_username != "Mavjud emas" else "Mavjud emas"
            
            # G'olibning o'ziga boradigan tabrik xabari
            congrats_text = (
                f"🎉 **URRAAA, SIZ G'OLIB BO'LDINGIZ!** 🎉\n\n"
                f"Hurmatli ishtirokchi, siz 'Kosonsoy Gullari' konkursida omadli **random** funksiyasi orqali tanlab olindingiz va konkursimiz g'oliblaridan biriga aylandingiz! 🏆\n\n"
                f"Sizning omadli ID raqamingiz: *{winner_id_number}*\n\n"
                "Yutuqni qabul qilib olish uchun yaqin daqiqalar ichida admin siz bilan bog'lanadi! Kanaldan chiqib ketmang. 🌸"
            )
            
            try:
                # G'olibga xabar yuborish
                await bot.send_message(chat_id=winner_user_id, text=congrats_text, parse_mode="Markdown")
                winner_notified = "✅ Xabar yetkazildi"
            except Exception:
                winner_notified = "❌ Xabar yuborilmadi (bloklagan)"
            
            # Admin uchun hisobot matnini shakllantiramiz
            admin_report += (
                f"🏅 **{index}-O'rin G'olibi:** {winner_id_number}-ID egasi\n"
                f"📞 Tel: {winner_phone}\n"
                f"👤 Profil: {user_link}\n"
                f"💬 Holat: {winner_notified}\n"
                f"----------------------------------\n"
            )
            await asyncio.sleep(0.1)
            
        # Adminga to'liq hisobotni yuboramiz
        await message.answer(admin_report, parse_mode="Markdown", reply_markup=get_admin_menu())

@dp.message(F.text == "✉️ Xabar tarqatish")
async def admin_broadcast_start(message: types.Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Barcha foydalanuvchilarga yuboriladigan xabar matnini kiriting:")
        # Botni foydalanuvchidan matn kutish holatiga o'tkazamiz
        await state.set_state(AdminStates.waiting_for_broadcast)

@dp.message(AdminStates.waiting_for_broadcast)
async def admin_broadcast_send(message: types.Message, state: FSMContext):
    # Faqat matnli xabarlarni tekshiramiz
    if not message.text:
        return await message.answer("Iltimos, faqat matnli xabar yuboring!")
        
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    
    # Holatni srazi tozalaymiz
    await state.clear()
    
    if not users:
        return await message.answer("Bazada foydalanuvchilar yo'q, xabar yuboriladigan odam topilmadi.", reply_markup=get_admin_menu())
        
    send_count = 0
    await message.answer("Xabar yuborish boshlandi, iltimos kuting...")
    
    for user in users:
        try:
            # user[0] qilib yozish shart, chunki tuple ichida keladi
            await bot.send_message(chat_id=user[0], text=message.text)
            send_count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
            
    await message.answer(f"Xabar tarqatildi. {send_count} ta foydalanuvchiga yetib bordi.", reply_markup=get_admin_menu())
    
# ============================================================
# 7. BOTNI ISHGA TUSHIRISH FUNKSIYASI (Aiogram 3 versiyada)
# ============================================================
async def main():
    print("Kosonsoy Gullari boti muvaffaqiyatli ishga tushmoqda...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

# ============================================================
# 8. RENDER TEKIN SERVERI UCHUN PORT BINDING (ORQA FONDA)
# ============================================================
def run_port():
    # Render tekin serveri talab qiladigan portni zaxiralash
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

# Port ochish xizmatini alohida oqimda (potok) yoqish
threading.Thread(target=run_port, daemon=True).start()

if __name__ == "__main__":
    asyncio.run(main())
