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
    # Проверяем есть ли параметр приглашения
    if message.text and len(message.text.split()) > 1:
        param = message.text.split()[1]
        
        # Если это инвайт-ссылка
        if param.startswith('invite_'):
            inviter_id = param.replace('invite_', '')
            invited_user_id = str(message.from_user.id)
            invited_username = message.from_user.username or message.from_user.first_name
            
            # Отправляем уведомление пригласившему
            try:
                await message.bot.send_message(
                    chat_id=inviter_id,
                    text=f"🎉 {invited_username} присоединился к вашим близким!\n\n"
                         f"Теперь вы можете добавить его в список близких."
                )
            except:
                pass  # Пользователь мог заблокировать бота
            
            # Сообщение приглашённому
            await message.answer(
                f"👋 Добро пожаловать!\n\n"
                f"Вы были приглашены пользователем. Теперь можете использовать бот для подбора подарков!",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(
                        text="🎁 Подобрать подарок",
                        web_app=types.WebAppInfo(url="https://timetoshame.github.io/GTW/frontend/index.html?v=9")
                    )]
                ])
            )
            return
    
    # Обычное приветствие
    await message.answer(
        "👋 Привет! Я помогу тебе подобрать идеальный подарок.\n\n"
        "Нажми на кнопку ниже, чтобы начать:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(
                text="🎁 Подобрать подарок",
                web_app=types.WebAppInfo(url="https://timetoshame.github.io/GTW/frontend/index.html?v=9")
            )]
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
    