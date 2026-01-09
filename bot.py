import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
import os

# Загружаем токен из .env файла
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Настройка логирования (чтобы видеть что происходит)
logging.basicConfig(level=logging.INFO)

# Создаём бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я помогу тебе подобрать идеальный подарок.\n\n"
        "Нажми на кнопку ниже, чтобы начать:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🎁 Подобрать подарок", callback_data="select_gift")]
        ])
    )

# Обработчик нажатия на кнопку
@dp.callback_query(lambda c: c.data == "select_gift")
async def process_select_gift(callback: types.CallbackQuery):
    await callback.message.answer("Скоро здесь откроется Mini App! 🚀")
    await callback.answer()

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    