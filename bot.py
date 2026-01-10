import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
import os
from database import db

# Загружаем токен из .env файла
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Создаём бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# URL Mini App
MINI_APP_URL = "https://timetoshame.github.io/GTW/frontend/index.html?v=11"

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    # Регистрируем пользователя в БД
    db.add_user(user_id, username, first_name)
    
    # Проверяем есть ли параметр приглашения
    if message.text and len(message.text.split()) > 1:
        param = message.text.split()[1]
        
        # Если это инвайт-ссылка
        if param.startswith('invite_'):
            inviter_id = param.replace('invite_', '')
            
            # Проверяем что пользователь не приглашает сам себя
            if inviter_id != user_id:
                # Записываем приглашение
                db.add_invitation(inviter_id, user_id)
                
                # Добавляем приглашённого в близкие пригласившего
                db.add_close_person(
                    owner_id=inviter_id,
                    name=first_name,
                    person_id=user_id
                )
                
                # Отправляем уведомление пригласившему
                try:
                    await bot.send_message(
                        chat_id=inviter_id,
                        text=f"🎉 {first_name} принял ваше приглашение!\n\n"
                             f"Он автоматически добавлен в ваш список близких."
                    )
                except Exception as e:
                    logging.error(f"Не удалось отправить уведомление: {e}")
                
                # Сообщение приглашённому
                await message.answer(
                    f"👋 Добро пожаловать, {first_name}!\n\n"
                    f"Вы приняли приглашение и теперь в списке близких вашего друга.\n"
                    f"Используйте бот для подбора подарков!",
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                        [types.InlineKeyboardButton(
                            text="🎁 Подобрать подарок",
                            web_app=types.WebAppInfo(url=MINI_APP_URL)
                        )]
                    ])
                )
                return
    
    # Обычное приветствие
    await message.answer(
        f"👋 Привет, {first_name}! Я помогу тебе подобрать идеальный подарок.\n\n"
        "Нажми на кнопку ниже, чтобы начать:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(
                text="🎁 Подобрать подарок",
                web_app=types.WebAppInfo(url=MINI_APP_URL)
            )]
        ])
    )

# Обработчик данных из Mini App
@dp.message(lambda message: message.web_app_data)
async def handle_web_app_data(message: types.Message):
    import json
    
    try:
        data = json.loads(message.web_app_data.data)
        
        # Здесь обрабатываем данные из Mini App
        name = data.get('name', 'Без имени')
        event = data.get('event', 'Не указано')
        budget = data.get('budget', '0')
        
        await message.answer(
            f"✅ Данные получены!\n\n"
            f"👤 Получатель: {name}\n"
            f"🎉 Событие: {event}\n"
            f"💰 Бюджет: {budget} ₽\n\n"
            f"🔄 Подбираю подарки..."
        )
        
        # TODO: Здесь будет логика подбора подарков с помощью AI
        
    except Exception as e:
        logging.error(f"Ошибка обработки данных: {e}")
        await message.answer("❌ Произошла ошибка при обработке данных")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())