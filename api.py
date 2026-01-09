from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import json
import hashlib
import hmac
from urllib.parse import parse_qs
from database import db
import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

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
    gender: Optional[str] = ''
    birthdate: Optional[str] = ''
    interests: Optional[str] = ''
    age: Optional[int] = None

class UpdatePerson(BaseModel):
    person_db_id: int
    name: Optional[str] = None
    gender: Optional[str] = None
    birthdate: Optional[str] = None
    interests: Optional[str] = None
    age: Optional[int] = None

class DeletePeople(BaseModel):
    person_db_ids: List[int]

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
    
    # Добавляем приглашённого в близкие пригласившего
    db.add_close_person(
        owner_id=inviter_id,
        name=invited_name,
        person_id=invited_id
    )
    
    return {"success": True, "message": "Invitation accepted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
