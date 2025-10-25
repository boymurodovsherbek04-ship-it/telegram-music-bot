import logging
from aiogram import Bot, Dispatcher, executor, types
import os

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("8248425244:AAEQI8sjsOYgGWtDxf72vfQ_tkNSTVmEMBs")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.answer("🎵 Salom! Men ishga tushdim va sizga musiqa yaratishga yordam bera olaman!")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
