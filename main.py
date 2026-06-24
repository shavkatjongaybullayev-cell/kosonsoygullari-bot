import os
import asyncio
import logging
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
# Tugmalar yaratish uchun kerakli modullar:
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# 1. LOGGING (Serverda xatoliklarni kuzatish uchun)
logging.basicConfig(level=logging.INFO)

# ============================================================
# 2. ASOSIY MA'LUMOTLAR (Shu yerga o'z ma'lumotlaringizni yozing)
# ============================================================
BOT_TOKEN = "8816635869:AAG5R7mv9dJS-H-LYAT7ALCY2PDp6hSEdBE"
ADMIN_ID = 644872296  # O'zingizning Telegram ID raqamingizni yozing (qo'shtirnoqsiz)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ============================================================
# 3. TUGMALAR (KEYBOARDS) - NAMUNA
# ============================================================
def get_main_menu():
    # Oddiy pastki tugmalar (Reply Keyboard)
    builder = ReplyKeyboardBuilder()
    builder.button(text="💐 Gullar katalogi")
    builder.button(text="📞 Biz bilan aloqa")
    builder.button(text="ℹ️ Ma'lumot")
    builder.adjust(2, 1) # Birinchi qatorda 2 ta, keyingisida 1 ta tugma
    return builder.as_markup(resize_keyboard=True)

def get_inline_menu():
    # Xabar tagida turadigan tugmalar (Inline Keyboard)
    builder = InlineKeyboardBuilder()
    builder.button(text="Buyurtma berish 🛒", callback_data="buyurtma")
    return builder.as_markup()

# ============================================================
# 4. XABARLARNI TUTUVCHI FUNKSIYALAR (HANDLERS)
# ============================================================

# /start buyrug'i kelganda
@dp.message(Command("start"))
async def start_command(message: types.Message):
    # Agar botga adminga yozsa, alohida salomlashadi
    if message.from_user.id == ADMIN_ID:
        await message.answer("Xush kelibsiz, Admin paneliga! 👑", reply_markup=get_main_menu())
    else:
        await message.answer(
            "Assalomu alaykum! Kosonsoy gullari botiga xush kelibsiz! 🌸", 
            reply_markup=get_main_menu()
        )

# "💐 Gullar katalogi" tugmasi bosilganda
@dp.message(lambda message: message.text == "💐 Gullar katalogi")
async def catalog_command(message: types.Message):
    await message.answer("Bizdagi mavjud gullar ro'yxati:", reply_markup=get_inline_menu())

# "📞 Biz bilan aloqa" tugmasi bosilganda
@dp.message(lambda message: message.text == "📞 Biz bilan aloqa")
async def contact_command(message: types.Message):
    await message.answer("Biz bilan bog'lanish uchun: +998900503362")

# Agar foydalanuvchi boshqa ixtiyoriy matn yozsa
@dp.message()
async def echo_command(message: types.Message):
    await message.reply(f"Siz yozdingiz: {message.text}")

# ============================================================
# 5. BOTNI ISHGA TUSHIRISH FUNKSIYASI
# ============================================================
async def main():
    print("Bot muvaffaqiyatli ishga tushdi...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

# ============================================================
# 6. RENDER SERVERI UCHUN MAJBURIY PORT OCHISH (ORQA FONDA)
# ============================================================
def run_port():
    # Render talab qiladigan portni orqa fonda band qilib turadi
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

# Port ochish xizmatini alohida oqimda yoqamiz
threading.Thread(target=run_port, daemon=True).start()

if __name__ == '__main__':
    asyncio.run(main())
