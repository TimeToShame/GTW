// menu.js - Боковое меню (sidebar)

(function() {
    'use strict';

    let sidebar = null;
    let overlay = null;
    let menuBtn = null;

    // Открыть меню
    function openMenu() {
        if (sidebar && overlay) {
            sidebar.classList.add('active');
            overlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }

    // Закрыть меню
    function closeMenu() {
        if (sidebar && overlay) {
            sidebar.classList.remove('active');
            overlay.classList.remove('active');
            document.body.style.overflow = '';
        }
    }

    // Переключить меню
    function toggleMenu() {
        if (sidebar && sidebar.classList.contains('active')) {
            closeMenu();
        } else {
            openMenu();
        }
    }

    // Создать HTML меню
    function createMenuHTML() {
        return `
            <div class="sidebar-overlay" id="sidebarOverlay"></div>
            <aside class="sidebar" id="sidebar">
                <div class="sidebar-header">
                    <span class="sidebar-logo">🎁</span>
                    <span class="sidebar-brand">WTG</span>
                </div>
                <nav class="sidebar-nav">
                    <div class="nav-group">
                        <a href="index.html" class="nav-item" data-page="index">
                            <span class="nav-item-icon">🏠</span>
                            <span class="nav-item-text">Главная</span>
                        </a>
                    </div>
                    
                    <div class="nav-group">
                        <div class="nav-group-title">Обо мне</div>
                        <a href="profile.html" class="nav-item" data-page="profile">
                            <span class="nav-item-icon">👤</span>
                            <span class="nav-item-text">Мой профиль</span>
                        </a>
                        <a href="wishlist.html" class="nav-item" data-page="wishlist">
                            <span class="nav-item-icon">⭐</span>
                            <span class="nav-item-text">Мой вишлист</span>
                        </a>
                    </div>
                    
                    <div class="nav-group">
                        <div class="nav-group-title">Близкие</div>
                        <a href="friends.html" class="nav-item" data-page="friends">
                            <span class="nav-item-icon">👥</span>
                            <span class="nav-item-text">Список близких</span>
                        </a>
                        <a href="gift-picker.html" class="nav-item" data-page="gift-picker">
                            <span class="nav-item-icon">🎁</span>
                            <span class="nav-item-text">Подбор подарков</span>
                        </a>
                        <a href="vip-gifts.html" class="nav-item" data-page="vip-gifts">
                            <span class="nav-item-icon">👑</span>
                            <span class="nav-item-text">VIP Подарки</span>
                        </a>
                    </div>
                </nav>
                <div class="sidebar-footer">
                    What To Gift v1.0
                </div>
            </aside>
        `;
    }

    // Подсветить активный пункт меню
    function highlightActivePage() {
        const currentPage = window.location.pathname.split('/').pop() || 'index.html';
        const pageName = currentPage.replace('.html', '');
        
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
            if (item.getAttribute('data-page') === pageName) {
                item.classList.add('active');
            }
        });
    }

    // Инициализация
    function init() {
        // Вставляем HTML меню в начало body
        document.body.insertAdjacentHTML('afterbegin', createMenuHTML());

        // Получаем элементы
        sidebar = document.getElementById('sidebar');
        overlay = document.getElementById('sidebarOverlay');
        menuBtn = document.getElementById('menuBtn');

        // Обработчики событий
        if (menuBtn) {
            menuBtn.addEventListener('click', toggleMenu);
        }

        if (overlay) {
            overlay.addEventListener('click', closeMenu);
        }

        // Закрытие по Escape
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeMenu();
            }
        });

        // Закрытие свайпом влево (для мобильных)
        let touchStartX = 0;
        if (sidebar) {
            sidebar.addEventListener('touchstart', function(e) {
                touchStartX = e.touches[0].clientX;
            });

            sidebar.addEventListener('touchmove', function(e) {
                const touchX = e.touches[0].clientX;
                const diff = touchStartX - touchX;
                
                if (diff > 50) {
                    closeMenu();
                }
            });
        }

        // Подсвечиваем активную страницу
        highlightActivePage();
    }

    // Запускаем когда DOM готов
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Экспортируем для использования в других скриптах
    window.AppMenu = {
        open: openMenu,
        close: closeMenu,
        toggle: toggleMenu
    };
})();
