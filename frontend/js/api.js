// api.js - Работа с API

(function() {
    'use strict';

    // URL API (Render)
    const API_BASE_URL = 'https://gtw-lq6s.onrender.com';

    // Получаем initData из Telegram
    function getInitData() {
        if (window.Telegram && window.Telegram.WebApp) {
            return window.Telegram.WebApp.initData;
        }
        return '';
    }

    // Получаем данные пользователя из Telegram
    function getTelegramUser() {
        if (window.Telegram && window.Telegram.WebApp) {
            return window.Telegram.WebApp.initDataUnsafe.user || null;
        }
        return null;
    }

    // Базовый запрос к API
    async function apiRequest(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const initData = getInitData();

        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': initData
            }
        };

        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };

        try {
            const response = await fetch(url, mergedOptions);
            
            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // === API МЕТОДЫ ===

    // Получить список близких
    async function getClosePeople() {
        return apiRequest('/api/close-people');
    }

    // Добавить близкого человека
    async function addClosePerson(data) {
        return apiRequest('/api/close-people', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // Обновить близкого человека
    async function updateClosePerson(data) {
        return apiRequest('/api/close-people', {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    // Удалить близких людей
    async function deleteClosePeople(personDbIds) {
        return apiRequest('/api/close-people', {
            method: 'DELETE',
            body: JSON.stringify({ person_db_ids: personDbIds })
        });
    }

    // Принять приглашение
    async function acceptInvitation(inviterId) {
        return apiRequest(`/api/invitation/${inviterId}`, {
            method: 'POST'
        });
    }

    // === ПРОФИЛЬ ===

    // Получить профиль
    async function getProfile() {
        return apiRequest('/api/profile');
    }

    // Обновить профиль
    async function updateProfile(data) {
        return apiRequest('/api/profile', {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    // === WISHLIST ===

    // Получить wishlist
    async function getWishlist() {
        return apiRequest('/api/wishlist');
    }

    // Добавить товар в wishlist
    async function addWishlistItem(data) {
        return apiRequest('/api/wishlist', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // Обновить товар в wishlist
    async function updateWishlistItem(data) {
        return apiRequest('/api/wishlist', {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    // Удалить товар из wishlist
    async function deleteWishlistItem(itemId) {
        return apiRequest(`/api/wishlist/${itemId}`, {
            method: 'DELETE'
        });
    }

    // === TELEGRAM WEBAPP ===

    // Инициализация Telegram WebApp
    function initTelegram() {
        if (window.Telegram && window.Telegram.WebApp) {
            const tg = window.Telegram.WebApp;
            tg.ready();
            tg.expand();
            return tg;
        }
        return null;
    }

    // Показать основную кнопку Telegram
    function showMainButton(text, callback) {
        if (window.Telegram && window.Telegram.WebApp) {
            const tg = window.Telegram.WebApp;
            tg.MainButton.setText(text);
            tg.MainButton.onClick(callback);
            tg.MainButton.show();
        }
    }

    // Скрыть основную кнопку
    function hideMainButton() {
        if (window.Telegram && window.Telegram.WebApp) {
            window.Telegram.WebApp.MainButton.hide();
        }
    }

    // Показать кнопку "Назад"
    function showBackButton(callback) {
        if (window.Telegram && window.Telegram.WebApp) {
            const tg = window.Telegram.WebApp;
            tg.BackButton.onClick(callback);
            tg.BackButton.show();
        }
    }

    // Скрыть кнопку "Назад"
    function hideBackButton() {
        if (window.Telegram && window.Telegram.WebApp) {
            window.Telegram.WebApp.BackButton.hide();
        }
    }

    // Закрыть WebApp
    function closeWebApp() {
        if (window.Telegram && window.Telegram.WebApp) {
            window.Telegram.WebApp.close();
        }
    }

    // Показать всплывающее сообщение
    function showAlert(message) {
        if (window.Telegram && window.Telegram.WebApp) {
            window.Telegram.WebApp.showAlert(message);
        } else {
            alert(message);
        }
    }

    // Показать подтверждение
    function showConfirm(message, callback) {
        if (window.Telegram && window.Telegram.WebApp) {
            window.Telegram.WebApp.showConfirm(message, callback);
        } else {
            const result = confirm(message);
            callback(result);
        }
    }

    // Экспортируем API
    window.API = {
        // Данные
        getInitData,
        getTelegramUser,

        // CRUD операции
        getClosePeople,
        addClosePerson,
        updateClosePerson,
        deleteClosePeople,
        acceptInvitation,

        // Профиль
        getProfile,
        updateProfile,

        // Wishlist
        getWishlist,
        addWishlistItem,
        updateWishlistItem,
        deleteWishlistItem,

        // Telegram WebApp
        initTelegram,
        showMainButton,
        hideMainButton,
        showBackButton,
        hideBackButton,
        closeWebApp,
        showAlert,
        showConfirm
    };
})();
