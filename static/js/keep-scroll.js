'use strict';
/* Сохранение прокрутки боковой навигации между переходами.
 *
 * Боковая панель TradeHub и панель разделов админки — самостоятельные
 * прокручиваемые области (``overflow: auto``). Браузер восстанавливает
 * прокрутку только у окна, поэтому после перехода панель откатывалась
 * к первому пункту: чтобы вернуться к нужному модулю, приходилось
 * прокручивать её заново.
 *
 * Скрипт запоминает ``scrollTop`` в ``sessionStorage`` (на вкладку —
 * ровно так же Django хранит фильтр в панели админки) и возвращает
 * положение после загрузки страницы.
 *
 * Разметка: элемент помечается атрибутом ``data-keep-scroll="<ключ>"``.
 * Боковая панель админки создаётся Django и атрибута не имеет, поэтому
 * находится по ``id``.
 */
{
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
            /* хранилище недоступно — прокрутку просто не запомним */
        }
    }

    const panels = collect();
    if (panels.length === 0) {
        return;
    }

    panels.forEach(([el, key]) => {
        let scheduled = false;
        el.addEventListener('scroll', () => {
            if (scheduled) {
                return;
            }
            scheduled = true;
            window.requestAnimationFrame(() => {
                scheduled = false;
                write(key, el.scrollTop);
            });
        }, {passive: true});
    });

    // Последний шанс перед уходом со страницы: клик может последовать
    // сразу за прокруткой, ещё до срабатывания requestAnimationFrame.
    window.addEventListener('pagehide', () => {
        panels.forEach(([el, key]) => write(key, el.scrollTop));
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
            // Плавная прокрутка превратила бы возврат в анимацию при
            // каждой загрузке страницы, поэтому на время возврата она
            // отключается.
            const previous = el.style.scrollBehavior;
            el.style.scrollBehavior = 'auto';
            el.scrollTop = top;
            el.style.scrollBehavior = previous;
            if (el.scrollTop < top) {
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
}
