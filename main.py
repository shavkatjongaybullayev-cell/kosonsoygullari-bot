import os
import asyncio
import logging
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# 1. LOGGING (Serverda bot qanday ishlayotganini ko'rish uchun)
logging.basicConfig(level=logging.INFO)

# 2. BOT TOKEN (O'zingizning tokeningizni qo'ying)
# Maslahat: Tokenni xavfsizlik uchun shu yerga to'g'ridan-to'g'ri yozib qo'ying
BOT_TOKEN = "8816635869:AAG5R7mv9dJS-H-LYAT7ALCY2PDp6hSEdBE"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 3. BOT BUYRUQLARI (Handlerlar)
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "Assalomu alaykum! Kosonsoy gullari botiga xush kelibsiz.\n"
        "Botingiz hozirda Render serverida muvaffaqiyatli ishlamoqda! 🚀"
    )

@dp.message()
async def echo_command(message: types.Message):
    # Foydalanuvchi yozgan har qanday matnga bot qaytarib javob beradi
    await message.reply(f"Siz yozdingiz: {message.text}")

# 4. BOTNI ISHGA TUSHIRISH FUNKSIYASI
async def main():
    print("Bot ishga tushmoqda...")
    # Bot eski kelgan xabarlarga javob qaytarmasligi uchun drop_pending_updates=True qilamiz
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

# ------------------------------------------------------------
# 5. RENDER TEKIN SERVERI UCHUN SOXTA PORT OCHISH (ORQA FONDA)
# ------------------------------------------------------------
def run_port():
    # Render avtomatik taqdim etadigan PORTni oladi, bo'lmasa 10000 ni ishlatadi
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    print(f"Soxta port xizmati {port}-portda ishga tushdi.")
    server.serve_forever()

# Portni alohida oqimda (potok) yoqamiz, Render "Port topilmadi" deb botni o'chirmasligi uchun
threading.Thread(target=run_port, daemon=True).start()

# Dasturni asosiy oqimda, xatosiz ishga tushirish qismi
if __name__ == '__main__':
    asyncio.run(main())
