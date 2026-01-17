# Гайд по деплою на Render

## ✅ Изменения запушены в GitHub

Коммит: `4b74ad4` - Add user profile page with wishlist functionality

---

## Автоматический деплой

Render автоматически подхватывает изменения из GitHub. Процесс:

1. **GitHub webhook** → триггерит деплой на Render
2. **Render** скачивает новый код
3. **База данных** - миграции выполнятся автоматически при старте
4. **Новые таблицы и колонки** будут созданы

---

## Что произойдет при деплое

### 1. База данных (автоматически)
При инициализации Database класса выполнятся миграции:
- ✅ Добавится `birthdate VARCHAR` в таблицу `users`
- ✅ Добавится `interests TEXT` в таблицу `users`
- ✅ Создастся таблица `wishlist` с полями:
  - id, user_id, title, description, price, url, image_url, created_at

### 2. API Endpoints (сразу доступны)
- `GET /api/profile` - получить профиль
- `PUT /api/profile` - обновить профиль
- `GET /api/wishlist` - получить wishlist
- `POST /api/wishlist` - добавить товар
- `PUT /api/wishlist` - обновить товар
- `DELETE /api/wishlist/{item_id}` - удалить товар

### 3. Frontend (сразу доступен)
- Новая страница: `https://gtw-lq6s.onrender.com/frontend/profile.html`
- Обновлённая навигация на всех страницах
- Исправлена адаптивность

---

## Проверка после деплоя

### 1. Проверить статус деплоя
Зайти на [Render Dashboard](https://dashboard.render.com/):
- Найти сервис `gtw`
- Дождаться статуса "Live"
- Проверить логи на наличие ошибок

### 2. Проверить API
```bash
# Проверка что API работает
curl https://gtw-lq6s.onrender.com/

# Должно вернуть:
# {"message": "Gift Bot API is running"}
```

### 3. Проверить в Telegram
1. Открыть бота: `@wtg_gift_bot`
2. Запустить Mini App
3. Нажать на иконку профиля (👤) в правом верхнем углу
4. Проверить:
   - ✅ Отображается имя из Telegram
   - ✅ Можно заполнить дату рождения
   - ✅ Можно добавить интересы
   - ✅ Можно добавить товары в wishlist
   - ✅ Кнопка "Поделиться" работает

---

## Если что-то пошло не так

### Проблема: Миграции не выполнились
**Решение**: Проверить логи Render на наличие ошибок миграции

### Проблема: 404 на profile.html
**Решение**: Проверить что файл задеплоился:
```bash
curl https://gtw-lq6s.onrender.com/frontend/profile.html
```

### Проблема: API возвращает 500
**Решение**:
1. Проверить логи Render
2. Убедиться что DATABASE_URL установлен
3. Проверить что миграции выполнились

### Откат к предыдущей версии
```bash
git revert HEAD
git push origin main
```

---

## Мониторинг

### Логи Render
```
https://dashboard.render.com/web/srv-YOUR-SERVICE-ID/logs
```

### Проверка базы данных
Можно подключиться к PostgreSQL через Render Dashboard:
```bash
# Из настроек сервиса скопировать External Database URL
psql <DATABASE_URL>

# Проверить таблицы
\dt

# Проверить колонки users
\d users

# Проверить wishlist
SELECT * FROM wishlist LIMIT 5;
```

---

## Следующие шаги

После успешного деплоя:

1. ✅ Протестировать все функции профиля в боте
2. ✅ Добавить несколько товаров в wishlist
3. ✅ Протестировать кнопку "Поделиться"
4. ✅ Проверить адаптивность на мобильном

### Возможные улучшения в будущем:
- AI парсинг товаров по URL
- Категории wishlist
- Приоритеты подарков
- Уведомления о днях рождения
