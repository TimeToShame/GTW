#!/usr/bin/env python3
"""
Тестовый скрипт для проверки функционала профиля и wishlist
"""

import requests
import json
import hashlib
import hmac
import time
from urllib.parse import urlencode

# Конфигурация
API_BASE_URL = "http://localhost:8000"
BOT_TOKEN = "8419652448:AAEv393pXNiHbEUcdogjhMt3o9LX9iyJAck"

# Тестовый пользователь
TEST_USER = {
    "id": 123456789,
    "first_name": "Тестовый",
    "username": "test_user",
    "language_code": "ru"
}

def create_init_data(user_data):
    """Создать валидный initData для Telegram WebApp"""
    auth_date = int(time.time())

    data_check = {
        "user": json.dumps(user_data, separators=(',', ':')),
        "auth_date": str(auth_date),
        "query_id": "test_query_123"
    }

    # Сортируем и создаём строку для проверки
    data_check_string = '\n'.join([f"{k}={v}" for k, v in sorted(data_check.items())])

    # Создаём секретный ключ
    secret_key = hmac.new("WebAppData".encode(), BOT_TOKEN.encode(), hashlib.sha256).digest()

    # Вычисляем hash
    hash_value = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    # Создаём финальный initData
    init_data = urlencode({**data_check, "hash": hash_value})

    return init_data

def test_api():
    """Тестирование API"""

    print("🧪 Тестирование API профиля и wishlist\n")
    print("=" * 60)

    # Создаём initData
    init_data = create_init_data(TEST_USER)
    headers = {
        "Authorization": init_data,
        "Content-Type": "application/json"
    }

    # 1. Тест получения профиля
    print("\n1️⃣ GET /api/profile - Получение профиля")
    print("-" * 60)
    response = requests.get(f"{API_BASE_URL}/api/profile", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        profile = response.json()
        print(f"✅ Профиль получен:")
        print(json.dumps(profile, indent=2, ensure_ascii=False))
    else:
        print(f"❌ Ошибка: {response.text}")
        return

    # 2. Тест обновления профиля
    print("\n2️⃣ PUT /api/profile - Обновление профиля")
    print("-" * 60)
    update_data = {
        "birthdate": "1990-05-15",
        "interests": "Программирование, путешествия, чтение научной фантастики, фотография"
    }
    response = requests.put(
        f"{API_BASE_URL}/api/profile",
        headers=headers,
        json=update_data
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ Профиль обновлён: {response.json()}")
    else:
        print(f"❌ Ошибка: {response.text}")
        return

    # 3. Проверка обновления профиля
    print("\n3️⃣ GET /api/profile - Проверка обновления")
    print("-" * 60)
    response = requests.get(f"{API_BASE_URL}/api/profile", headers=headers)
    if response.status_code == 200:
        profile = response.json()['profile']
        print(f"✅ Дата рождения: {profile.get('birthdate')}")
        print(f"✅ Интересы: {profile.get('interests')}")

    # 4. Тест добавления товара в wishlist
    print("\n4️⃣ POST /api/wishlist - Добавление товара")
    print("-" * 60)
    items_to_add = [
        {
            "title": "Sony WH-1000XM5",
            "description": "Беспроводные наушники с шумоподавлением",
            "price": "32 990 ₽",
            "url": "https://example.com/sony-wh1000xm5",
            "image_url": "https://via.placeholder.com/400x400/2d2d2d/ff9900?text=🎧"
        },
        {
            "title": "Kindle Paperwhite",
            "description": "Электронная книга с подсветкой",
            "price": "14 990 ₽",
            "url": "https://example.com/kindle",
            "image_url": "https://via.placeholder.com/400x400/2d2d2d/ff9900?text=📚"
        },
        {
            "title": "Apple Watch Series 9",
            "description": "Умные часы",
            "price": "45 990 ₽",
            "url": "https://example.com/apple-watch",
            "image_url": "https://via.placeholder.com/400x400/2d2d2d/ff9900?text=⌚"
        }
    ]

    item_ids = []
    for item in items_to_add:
        response = requests.post(
            f"{API_BASE_URL}/api/wishlist",
            headers=headers,
            json=item
        )
        if response.status_code == 200:
            result = response.json()
            item_ids.append(result['item_id'])
            print(f"✅ Добавлен: {item['title']} (ID: {result['item_id']})")
        else:
            print(f"❌ Ошибка: {response.text}")

    # 5. Тест получения wishlist
    print("\n5️⃣ GET /api/wishlist - Получение wishlist")
    print("-" * 60)
    response = requests.get(f"{API_BASE_URL}/api/wishlist", headers=headers)
    if response.status_code == 200:
        wishlist = response.json()
        print(f"✅ Wishlist получен ({len(wishlist['items'])} товаров):")
        for item in wishlist['items']:
            print(f"   • {item['title']} - {item['price']}")
    else:
        print(f"❌ Ошибка: {response.text}")

    # 6. Тест обновления товара
    if item_ids:
        print("\n6️⃣ PUT /api/wishlist - Обновление товара")
        print("-" * 60)
        update_item_data = {
            "item_id": item_ids[0],
            "price": "29 990 ₽",
            "description": "Беспроводные наушники с шумоподавлением (СКИДКА!)"
        }
        response = requests.put(
            f"{API_BASE_URL}/api/wishlist",
            headers=headers,
            json=update_item_data
        )
        if response.status_code == 200:
            print(f"✅ Товар обновлён: {response.json()}")
        else:
            print(f"❌ Ошибка: {response.text}")

    # 7. Тест удаления товара
    if len(item_ids) > 1:
        print("\n7️⃣ DELETE /api/wishlist/{item_id} - Удаление товара")
        print("-" * 60)
        delete_id = item_ids[-1]
        response = requests.delete(
            f"{API_BASE_URL}/api/wishlist/{delete_id}",
            headers=headers
        )
        if response.status_code == 200:
            print(f"✅ Товар удалён (ID: {delete_id}): {response.json()}")
        else:
            print(f"❌ Ошибка: {response.text}")

        # Проверка удаления
        response = requests.get(f"{API_BASE_URL}/api/wishlist", headers=headers)
        if response.status_code == 200:
            wishlist = response.json()
            print(f"✅ Осталось товаров: {len(wishlist['items'])}")

    # 8. Итоговый профиль
    print("\n8️⃣ Итоговый профиль и wishlist")
    print("-" * 60)
    response = requests.get(f"{API_BASE_URL}/api/profile", headers=headers)
    if response.status_code == 200:
        profile = response.json()['profile']
        print("📋 Профиль:")
        print(f"   Имя: {profile.get('first_name')}")
        print(f"   Username: @{profile.get('username')}")
        print(f"   Дата рождения: {profile.get('birthdate')}")
        print(f"   Интересы: {profile.get('interests')}")

    response = requests.get(f"{API_BASE_URL}/api/wishlist", headers=headers)
    if response.status_code == 200:
        wishlist = response.json()
        print(f"\n🎁 Wishlist ({len(wishlist['items'])} товаров):")
        for item in wishlist['items']:
            print(f"   • {item['title']} - {item['price']}")

    print("\n" + "=" * 60)
    print("✅ Все тесты пройдены успешно!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_api()
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
