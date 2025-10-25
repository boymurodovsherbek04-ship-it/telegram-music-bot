import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Tokenni shu yerga kiriting
BOT_TOKEN = "8248425244:AAGSTf0gCNejx2b8ACqRJ5BmbUzvL_cP63I"

# Log sozlamalari
logging.basicConfig(level=logging.INFO)

# Bot va dispatcher yaratish
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# /start komandasi uchun javob
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("🎵 Salom! Men ishlayapman! Bot muvaffaqiyatli ulandi!")

# Asosiy ishga tushirish funksiyasi
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
