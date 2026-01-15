// theme.js - Определение и применение темы Telegram

(function() {
    'use strict';

    // Определяем тему
    function detectTheme() {
        // Проверяем Telegram WebApp
        if (window.Telegram && window.Telegram.WebApp) {
            const tg = window.Telegram.WebApp;
            const colorScheme = tg.colorScheme; // 'light' или 'dark'
            return colorScheme || 'light';
        }
        
        // Fallback на системные настройки
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        
        return 'light';
    }

    // Применяем тему
    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        console.log('Theme applied:', theme);
    }

    // Инициализация при загрузке
    function init() {
        const theme = detectTheme();
        applyTheme(theme);

        // Слушаем изменения темы в Telegram
        if (window.Telegram && window.Telegram.WebApp) {
            window.Telegram.WebApp.onEvent('themeChanged', function() {
                const newTheme = detectTheme();
                applyTheme(newTheme);
            });
        }

        // Слушаем системные изменения темы (fallback)
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
                if (!window.Telegram || !window.Telegram.WebApp) {
                    applyTheme(e.matches ? 'dark' : 'light');
                }
            });
        }
    }

    // Запускаем когда DOM готов
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Экспортируем для использования в других скриптах
    window.AppTheme = {
        detect: detectTheme,
        apply: applyTheme,
        current: function() {
            return document.documentElement.getAttribute('data-theme') || 'light';
        }
    };
})();
