'use strict';
/* Сохранение положения в боковой навигации между переходами.
 *
 * Боковая панель TradeHub и панель разделов админки — самостоятельные
 * прокручиваемые области (``overflow: auto``). Браузер восстанавливает
 * прокрутку только у окна, поэтому после перехода панель откатывалась
 * к первому пункту: чтобы вернуться к нужному модулю, приходилось
 * прокручивать её заново.
 *
 * Есть второй случай, и он не очевиден. В узком окне
 * (``@media (max-width: 900px)``) панель растягивается —
 * ``position: static; max-height: none`` — и перестаёт прокручиваться
 * сама: прокручивается вся страница, а панель тянется на полторы тысячи
 * пикселей перед содержимым. Тогда нужно сохранять не ``scrollTop``
 * панели, а прокрутку окна — иначе переход всё равно выбрасывает
 * наверх. Оба случая различимы на месте: панель прокручивается сама
 * тогда и только тогда, когда содержимое выше неё.
 *
 * Значение хранится в ``sessionStorage`` (на вкладку — ровно так же
 * Django хранит фильтр в панели админки).
 *
 * Разметка: элемент помечается атрибутом ``data-keep-scroll="<ключ>"``.
 * Боковая панель админки создаётся Django и атрибута не имеет, поэтому
 * находится по ``id``.
 *
 * Весь код — в немедленно вызываемой функции. Это не стиль, а
 * необходимость: ``return`` вне функции недопустим в обычном скрипте,
 * и файл с ним целиком не выполняется в браузере (``node --check``
 * такой ошибки не показывает — он оборачивает файл в функцию).
 */
(function () {
    const PREFIX = 'tradehub.scroll.';

    function collect() {
        const found = [];
        document.querySelectorAll('[data-keep-scroll]').forEach((el) => {
            found.push([el, PREFIX + el.getAttribute('data-keep-scroll')]);
        });
        const adminNav = document.getElementById('nav-sidebar');
        if (adminNav && !adminNav.hasAttribute('data-keep-scroll')) {
            found.push([adminNav, PREFIX + 'admin-nav']);
        }
        return found;
    }

    function read(key) {
        try {
            return sessionStorage.getItem(key);
        } catch (err) {
            return null;              // приватный режим: хранилище запрещено
        }
    }

    function write(key, value) {
        try {
            sessionStorage.setItem(key, String(value));
        } catch (err) {
            /* хранилище недоступно — положение просто не запомним */
        }
    }

    /** Панель прокручивается сама, только если содержимое выше неё. */
    function scrollsItself(el) {
        return el.scrollHeight > el.clientHeight + 1;
    }

    /** Где сейчас находится навигация: внутри панели или на странице. */
    function positionOf(el) {
        return scrollsItself(el) ? el.scrollTop : window.scrollY;
    }

    function applyPosition(el, top) {
        if (scrollsItself(el)) {
            // Плавная прокрутка превратила бы возврат в анимацию при
            // каждой загрузке страницы, поэтому на время возврата она
            // отключается.
            const previous = el.style.scrollBehavior;
            el.style.scrollBehavior = 'auto';
            el.scrollTop = top;
            el.style.scrollBehavior = previous;
            return el.scrollTop >= top - 1;
        }

        // Панель растянута: вернуть нужно прокрутку страницы. Но только
        // если уходили, видя навигацию, — иначе это был переход из
        // содержимого, и возвращать читателя к панели не нужно.
        const rect = el.getBoundingClientRect();
        const navTop = rect.top + window.scrollY;
        const navBottom = navTop + el.offsetHeight;
        if (top > navBottom || top + window.innerHeight <= navTop) {
            return true;
        }
        const root = document.documentElement;
        const previous = root.style.scrollBehavior;
        root.style.scrollBehavior = 'auto';
        window.scrollTo(0, top);
        root.style.scrollBehavior = previous;
        return Math.abs(window.scrollY - top) <= 2;
    }

    const panels = collect();
    if (panels.length === 0) {
        return;
    }

    // Прокручивать могут и саму панель, и страницу — слушаем обе.
    let scheduled = false;
    function schedule() {
        if (scheduled) {
            return;
        }
        scheduled = true;
        window.requestAnimationFrame(() => {
            scheduled = false;
            panels.forEach(([el, key]) => write(key, positionOf(el)));
        });
    }

    panels.forEach(([el]) => {
        el.addEventListener('scroll', schedule, { passive: true });
    });
    window.addEventListener('scroll', schedule, { passive: true });

    // Последний шанс перед уходом со страницы: клик может последовать
    // сразу за прокруткой, ещё до срабатывания requestAnimationFrame.
    window.addEventListener('pagehide', () => {
        panels.forEach(([el, key]) => write(key, positionOf(el)));
    });

    let settled = false;

    function restoreAll() {
        if (settled) {
            return;
        }
        let pending = false;
        panels.forEach(([el, key]) => {
            const saved = read(key);
            if (saved === null) {
                return;
            }
            const top = parseInt(saved, 10);
            if (!(top > 0)) {
                return;
            }
            if (!applyPosition(el, top)) {
                pending = true;       // содержимое ещё не разложено
            }
        });
        settled = !pending;
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', restoreAll);
    } else {
        restoreAll();
    }
    // Второй проход — после полной загрузки: высота панели задана через
    // calc(100vh …), и к этому моменту она вычислена окончательно.
    // Повторяется только если первый возврат не удался.
    window.addEventListener('load', restoreAll);
})();
