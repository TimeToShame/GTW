from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import json
import hashlib
import hmac
from urllib.parse import parse_qs
from database_pg import db
import os
from dotenv import load_dotenv
import httpx
import re

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

app = FastAPI()

# CORS для работы с Telegram Mini App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === МОДЕЛИ ДАННЫХ ===

class ClosePerson(BaseModel):
    name: str
    person_id: Optional[str] = None
    relation: Optional[str] = ''
    gender: Optional[str] = ''
    birthdate: Optional[str] = ''
    interests: Optional[str] = ''
    age: Optional[int] = None

class UpdatePerson(BaseModel):
    person_db_id: int
    name: Optional[str] = None
    relation: Optional[str] = None
    gender: Optional[str] = None
    birthdate: Optional[str] = None
    interests: Optional[str] = None
    age: Optional[int] = None

class DeletePeople(BaseModel):
    person_db_ids: List[int]

class UpdateProfile(BaseModel):
    birthdate: Optional[str] = None
    interests: Optional[str] = None
    photo_url: Optional[str] = None

class WishlistItem(BaseModel):
    title: str
    description: Optional[str] = ''
    price: Optional[str] = ''
    url: Optional[str] = ''
    image_url: Optional[str] = ''

class UpdateWishlistItem(BaseModel):
    item_id: int
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None

class ParseUrlRequest(BaseModel):
    url: str

class BookGiftRequest(BaseModel):
    item_id: int

class PersonalGiftIdeaCreate(BaseModel):
    for_person_id: str
    title: str
    description: Optional[str] = ''
    price: Optional[str] = ''
    url: Optional[str] = ''
    image_url: Optional[str] = ''

class UpdatePersonalGiftIdea(BaseModel):
    idea_id: int
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None

class GiftSuggestionsRequest(BaseModel):
    person_name: str
    person_gender: Optional[str] = ''
    person_age: Optional[int] = None
    person_interests: Optional[str] = ''
    event: Optional[str] = ''
    budget_from: Optional[str] = ''
    budget_to: Optional[str] = ''
    additional_wishes: Optional[str] = ''

# === ПРОВЕРКА TELEGRAM INIT DATA ===

def validate_init_data(init_data: str) -> dict:
    """Проверка подлинности данных от Telegram"""
    try:
        parsed_data = parse_qs(init_data)
        
        # Извлекаем hash
        received_hash = parsed_data.get('hash', [''])[0]
        
        # Удаляем hash из данных
        data_to_check = {k: v[0] for k, v in parsed_data.items() if k != 'hash'}
        
        # Создаём строку для проверки
        data_check_string = '\n'.join([f"{k}={v}" for k, v in sorted(data_to_check.items())])
        
        # Создаём секретный ключ
        secret_key = hmac.new("WebAppData".encode(), BOT_TOKEN.encode(), hashlib.sha256).digest()
        
        # Вычисляем hash
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        # Проверяем
        if calculated_hash != received_hash:
            raise HTTPException(status_code=403, detail="Invalid init data")
        
        # Парсим user
        user = json.loads(data_to_check.get('user', '{}'))
        
        return user
    
    except Exception as e:
        raise HTTPException(status_code=403, detail=f"Validation error: {str(e)}")

# === API ENDPOINTS ===

@app.get("/")
async def root():
    return {"message": "Gift Bot API is running"}

@app.get("/api/close-people")
async def get_close_people(authorization: Optional[str] = Header(None)):
    """Получить всех близких пользователя"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    user = validate_init_data(authorization)
    user_id = str(user.get('id'))
    
    # Регистрируем пользователя если его нет
    db.add_user(user_id, user.get('username'), user.get('first_name'))
    
    # Получаем близких
    people = db.get_close_people(user_id)
    
    return {"people": people}

@app.post("/api/close-people")
async def add_close_person(person: ClosePerson, authorization: Optional[str] = Header(None)):
    """Добавить близкого человека"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    user = validate_init_data(authorization)
    user_id = str(user.get('id'))
    
    # Добавляем человека
    person_db_id = db.add_close_person(
        owner_id=user_id,
        name=person.name,
        person_id=person.person_id,
        relation=person.relation,
        gender=person.gender,
        birthdate=person.birthdate,
        interests=person.interests,
        age=person.age
    )
    
    return {"success": True, "person_db_id": person_db_id}

@app.put("/api/close-people")
async def update_close_person(update: UpdatePerson, authorization: Optional[str] = Header(None)):
    """Обновить данные близкого человека"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    user = validate_init_data(authorization)
    
    # Создаём словарь с обновлениями
    updates = {}
    if update.name is not None:
        updates['name'] = update.name
    if update.relation is not None:
        updates['relation'] = update.relation
    if update.gender is not None:
        updates['gender'] = update.gender
    if update.birthdate is not None:
        updates['birthdate'] = update.birthdate
    if update.interests is not None:
        updates['interests'] = update.interests
    if update.age is not None:
        updates['age'] = update.age
    
    db.update_close_person(update.person_db_id, **updates)
    
    return {"success": True}

@app.delete("/api/close-people")
async def delete_close_people(delete: DeletePeople, authorization: Optional[str] = Header(None)):
    """Удалить близких людей"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")

    user = validate_init_data(authorization)

    db.delete_close_people(delete.person_db_ids)

    return {"success": True}

@app.post("/api/close-people/remove-duplicates")
async def remove_duplicate_close_people(authorization: Optional[str] = Header(None)):
    """Удалить дубликаты близких людей"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")

    user = validate_init_data(authorization)
    user_id = str(user.get('id'))

    removed_count = db.remove_duplicate_close_people(user_id)

    return {"success": True, "removed_count": removed_count}

@app.post("/api/invitation/{inviter_id}")
async def accept_invitation(inviter_id: str, authorization: Optional[str] = Header(None)):
    """Принять приглашение"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")

    user = validate_init_data(authorization)
    invited_id = str(user.get('id'))
    invited_name = user.get('first_name', 'Пользователь')

    # Регистрируем обоих пользователей
    db.add_user(invited_id, user.get('username'), user.get('first_name'))

    # Записываем приглашение
    db.add_invitation(inviter_id, invited_id)

    # Получаем данные пригласившего
    inviter = db.get_user(inviter_id)
    inviter_name = inviter.get('first_name', 'Пользователь') if inviter else 'Пользователь'

    # Добавляем приглашённого в близкие пригласившего
    db.add_close_person(
        owner_id=inviter_id,
        name=invited_name,
        person_id=invited_id
    )

    # ВЗАИМНОСТЬ: Добавляем пригласившего в близкие приглашённого
    db.add_close_person(
        owner_id=invited_id,
        name=inviter_name,
        person_id=inviter_id
    )

    return {"success": True, "message": "Invitation accepted"}

# === ПРОФИЛЬ ===

@app.get("/api/profile")
async def get_profile(authorization: Optional[str] = Header(None)):
    """Получить профиль пользователя"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")

    user = validate_init_data(authorization)
    user_id = str(user.get('id'))

    # Регистрируем/обновляем пользователя
    db.add_user(user_id, user.get('username'), user.get('first_name'))

    # Получаем полный профиль
    profile = db.get_user(user_id)

    return {"profile": profile}

@app.put("/api/profile")
async def update_profile(update: UpdateProfile, authorization: Optional[str] = Header(None)):
    """Обновить профиль пользователя"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")

    user = validate_init_data(authorization)
    user_id = str(user.get('id'))

    # Обновляем профиль
    db.update_user_profile(
        user_id,
        birthdate=update.birthdate,
        interests=update.interests,
        photo_url=update.photo_url
    )

    return {"success": True}

# === WISHLIST ===

@app.get("/api/wishlist")
async def get_wishlist(authorization: Optional[str] = Header(None)):
    """Получить wishlist пользователя"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")

    user = validate_init_data(authorization)
    user_id = str(user.get('id'))

    items = db.get_wishlist(user_id)

    return {"items": items}

@app.post("/api/wishlist")
async def add_wishlist_item(item: WishlistItem, authorization: Optional[str] = Header(None)):
    """Добавить товар в wishlist"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")

    user = validate_init_data(authorization)
    user_id = str(user.get('id'))

    item_id = db.add_wishlist_item(
        user_id=user_id,
        title=item.title,
        description=item.description,
        price=item.price,
        url=item.url,
        image_url=item.image_url
    )

    return {"success": True, "item_id": item_id}

@app.put("/api/wishlist")
async def update_wishlist_item(update: UpdateWishlistItem, authorization: Optional[str] = Header(None)):
    """Обновить товар в wishlist"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")

    user = validate_init_data(authorization)

    updates = {}
    if update.title is not None:
        updates['title'] = update.title
    if update.description is not None:
        updates['description'] = update.description
    if update.price is not None:
        updates['price'] = update.price
    if update.url is not None:
        updates['url'] = update.url
    if update.image_url is not None:
        updates['image_url'] = update.image_url

    db.update_wishlist_item(update.item_id, **updates)

    return {"success": True}

@app.delete("/api/wishlist/{item_id}")
async def delete_wishlist_item(item_id: int, authorization: Optional[str] = Header(None)):
    """Удалить товар из wishlist"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")

    user = validate_init_data(authorization)

    db.delete_wishlist_item(item_id)

    return {"success": True}

# === ПАРСИНГ URL ===

@app.post("/api/parse-url")
async def parse_product_url(request: ParseUrlRequest, authorization: Optional[str] = Header(None)):
    """Парсинг товара по URL с помощью AI"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")

    validate_init_data(authorization)

    try:
        # Получаем содержимое страницы
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(request.url, follow_redirects=True)
            html_content = response.text

        # Извлекаем title страницы для базового случая
        title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE)
        page_title = title_match.group(1) if title_match else "Товар"

        # Ограничиваем размер HTML для AI (берём первые 8000 символов)
        html_snippet = html_content[:8000]

        # Запрос к AI для извлечения данных о товаре
        prompt = f"""Проанализируй HTML страницы товара и извлеки следующую информацию:
1. Название товара
2. Цена (с валютой)
3. Краткое описание (1-2 предложения)
4. URL изображения товара (главное фото)

URL страницы: {request.url}
Title страницы: {page_title}

HTML (фрагмент):
{html_snippet}

Верни ответ СТРОГО в формате JSON без дополнительного текста:
{{
  "title": "название товара",
  "price": "цена с валютой",
  "description": "краткое описание",
  "image_url": "URL изображения или null"
}}"""

        async with httpx.AsyncClient(timeout=30.0) as client:
            ai_response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://gtw-lq6s.onrender.com",
                    "X-Title": "WTG URL Parser"
                },
                json={
                    "model": "google/gemini-2.0-flash-exp:free",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3
                }
            )

        ai_data = ai_response.json()
        ai_content = ai_data["choices"][0]["message"]["content"]

        # Извлекаем JSON из ответа AI
        json_match = re.search(r'\{[\s\S]*\}', ai_content)
        if json_match:
            product_data = json.loads(json_match.group(0))
        else:
            # Fallback если AI не вернул JSON
            product_data = {
                "title": page_title,
                "price": "",
                "description": "",
                "image_url": None
            }

        return {
            "success": True,
            "data": product_data
        }

    except Exception as e:
        # В случае ошибки возвращаем базовые данные
        return {
            "success": False,
            "error": str(e),
            "data": {
                "title": page_title if 'page_title' in locals() else "Товар",
                "price": "",
                "description": "",
                "image_url": None
            }
        }

# === WISHLIST БЛИЗКИХ И БРОНИРОВАНИЕ ===

@app.get("/api/person/{person_id}/wishlist")
async def get_person_wishlist(person_id: str, authorization: Optional[str] = Header(None)):
    """Получить wishlist близкого человека с учётом бронирований"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")

    user = validate_init_data(authorization)
    viewer_id = str(user.get('id'))

    # Получаем wishlist с бронированиями
    items = db.get_wishlist_with_bookings(person_id, viewer_id)

    return {"items": items}

@app.post("/api/book-gift")
async def book_gift(request: BookGiftRequest, authorization: Optional[str] = Header(None)):
    """Забронировать подарок"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")

    user = validate_init_data(authorization)
    user_id = str(user.get('id'))

    booking_id = db.book_gift(request.item_id, user_id)

    if booking_id is None:
        raise HTTPException(status_code=400, detail="Gift already booked")

    return {"success": True, "booking_id": booking_id}

@app.delete("/api/book-gift/{item_id}")
async def unbook_gift(item_id: int, authorization: Optional[str] = Header(None)):
    """Отменить бронирование подарка"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")

    user = validate_init_data(authorization)
    user_id = str(user.get('id'))

    success = db.unbook_gift(item_id, user_id)

    if not success:
        raise HTTPException(status_code=404, detail="Booking not found")

    return {"success": True}

@app.get("/api/booked-count")
async def get_booked_count(authorization: Optional[str] = Header(None)):
    """Получить количество забронированных подарков пользователя"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")

    user = validate_init_data(authorization)
    user_id = str(user.get('id'))

    count = db.get_booked_count(user_id)

    return {"count": count}

# === ЛИЧНЫЕ ИДЕИ ПОДАРКОВ ===

@app.get("/api/personal-ideas/{for_person_id}")
async def get_personal_ideas(for_person_id: str, authorization: Optional[str] = Header(None)):
    """Получить мои идеи подарков для конкретного близкого"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")

    user = validate_init_data(authorization)
    user_id = str(user.get('id'))

    ideas = db.get_personal_gift_ideas(user_id, for_person_id)

    return {"ideas": ideas}

@app.post("/api/personal-ideas")
async def add_personal_idea(idea: PersonalGiftIdeaCreate, authorization: Optional[str] = Header(None)):
    """Добавить личную идею подарка"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")

    user = validate_init_data(authorization)
    user_id = str(user.get('id'))

    idea_id = db.add_personal_gift_idea(
        owner_id=user_id,
        for_person_id=idea.for_person_id,
        title=idea.title,
        description=idea.description,
        price=idea.price,
        url=idea.url,
        image_url=idea.image_url
    )

    return {"success": True, "idea_id": idea_id}

@app.put("/api/personal-ideas")
async def update_personal_idea(update: UpdatePersonalGiftIdea, authorization: Optional[str] = Header(None)):
    """Обновить личную идею подарка"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")

    user = validate_init_data(authorization)

    updates = {}
    if update.title is not None:
        updates['title'] = update.title
    if update.description is not None:
        updates['description'] = update.description
    if update.price is not None:
        updates['price'] = update.price
    if update.url is not None:
        updates['url'] = update.url
    if update.image_url is not None:
        updates['image_url'] = update.image_url

    db.update_personal_gift_idea(update.idea_id, **updates)

    return {"success": True}

@app.delete("/api/personal-ideas/{idea_id}")
async def delete_personal_idea(idea_id: int, authorization: Optional[str] = Header(None)):
    """Удалить личную идею подарка"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")

    user = validate_init_data(authorization)

    db.delete_personal_gift_idea(idea_id)

    return {"success": True}

# === ПОДБОР ПОДАРКОВ С AI ===

@app.post("/api/suggest-gifts")
async def suggest_gifts(request: GiftSuggestionsRequest, authorization: Optional[str] = Header(None)):
    """Подбор подарков с помощью AI"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")

    validate_init_data(authorization)

    # Маппинг событий
    event_names = {
        'birthday': 'День рождения',
        'new_year': 'Новый год',
        'feb23': '23 февраля',
        'mar8': '8 марта',
        'wedding': 'Свадьба',
        'anniversary': 'Годовщина',
        'valentines': 'День влюблённых',
        'just_because': 'Просто так'
    }

    # Формируем промпт
    prompt = f"""Ты - эксперт по подбору подарков. Подбери 20 идей подарков.

Информация о получателе:
- Имя: {request.person_name}
- Пол: {request.person_gender if request.person_gender == 'm' else 'женский' if request.person_gender == 'f' else 'не указан'}
- Возраст: {request.person_age or 'не указан'}
- Интересы: {request.person_interests or 'не указаны'}"""

    if request.event:
        prompt += f"\n- Событие: {event_names.get(request.event, request.event)}"

    if request.budget_from or request.budget_to:
        prompt += f"\n- Бюджет: {request.budget_from or '0'} - {request.budget_to or '∞'} рублей"

    if request.additional_wishes:
        prompt += f"\n- Дополнительные пожелания: {request.additional_wishes}"

    prompt += """

ВАЖНО: Ответ дай СТРОГО в формате JSON массива, без markdown, без пояснений, только JSON:
[
  {
    "name": "Название подарка",
    "description": "Краткое описание почему это хороший подарок (1-2 предложения)",
    "price": "примерная цена в рублях (только число)"
  }
]

Подбери разнообразные подарки в разных ценовых категориях. Учитывай пол, возраст и интересы."""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            ai_response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://gtw-lq6s.onrender.com",
                    "X-Title": "WTG Gift Picker"
                },
                json={
                    "model": "google/gemini-2.0-flash-exp:free",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.8
                }
            )

        if not ai_response.is_success:
            raise HTTPException(status_code=500, detail=f"AI API error: {ai_response.status_code}")

        ai_data = ai_response.json()
        ai_content = ai_data["choices"][0]["message"]["content"]

        # Парсим ответ
        cleaned = ai_content.strip()
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]
        if cleaned.startswith('```'):
            cleaned = cleaned[3:]
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        gifts = json.loads(cleaned)

        return {"success": True, "gifts": gifts}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating suggestions: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)