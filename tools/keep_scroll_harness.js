/* Проверка логики static/js/keep-scroll.js без браузера.
 *
 * Подменяет минимальный набор DOM API (панель с настоящим scrollTop,
 * sessionStorage, события) и прогоняет сценарии «прокрутил → перешёл →
 * вернулся». Запуск:
 *   node keep_scroll_harness.js <путь к keep-scroll.js>
 */
'use strict';
const fs = require('fs');
const assert = require('assert');

const target = process.argv[2];
const CODE = fs.readFileSync(target, 'utf8');

// ---------------------------------------------------------------- окружение

function makePanel({ attrs = {}, id = null, scrollHeight = 2000, clientHeight = 800 } = {}) {
    let top = 0;
    const listeners = {};
    const panel = {
        id,
        style: {},
        scrollHeight,
        clientHeight,
        get scrollTop() {
            return top;
        },
        set scrollTop(value) {
            // настоящая прокрутка упирается в предел содержимого;
            // высоты читаются с самого элемента, а не из замыкания,
            // чтобы тест мог «дорастить» содержимое после первой попытки
            top = Math.max(0, Math.min(value, panel.scrollHeight - panel.clientHeight));
        },
        getAttribute: (name) => (name in attrs ? attrs[name] : null),
        hasAttribute: (name) => name in attrs,
        addEventListener: (type, fn) => {
            (listeners[type] = listeners[type] || []).push(fn);
        },
        fire: (type) => {
            (listeners[type] || []).forEach((fn) => fn({}));
        },
    };
    return panel;
}

function makeStorage(backing) {
    return {
        getItem: (key) => (backing.has(key) ? backing.get(key) : null),
        setItem: (key, value) => backing.set(key, String(value)),
    };
}

/** Одна «загрузка страницы»: свежие document/window, общее хранилище. */
function loadPage(panels, backing, { readyState = 'loading' } = {}) {
    const rafQueue = [];
    const docListeners = {};
    const winListeners = {};

    const document = {
        readyState,
        querySelectorAll: (selector) =>
            selector === '[data-keep-scroll]'
                ? panels.filter((p) => p.hasAttribute('data-keep-scroll'))
                : [],
        getElementById: (id) => panels.find((p) => p.id === id) || null,
        addEventListener: (type, fn) => {
            (docListeners[type] = docListeners[type] || []).push(fn);
        },
    };
    const window = {
        requestAnimationFrame: (fn) => rafQueue.push(fn),
        addEventListener: (type, fn) => {
            (winListeners[type] = winListeners[type] || []).push(fn);
        },
    };

    new Function('document', 'window', 'sessionStorage', CODE)(
        document, window, makeStorage(backing));

    return {
        flushFrames: () => {
            while (rafQueue.length) {
                rafQueue.shift()();
            }
        },
        domReady: () => (docListeners.DOMContentLoaded || []).forEach((fn) => fn({})),
        fireLoad: () => (winListeners.load || []).forEach((fn) => fn({})),
        firePageHide: () => (winListeners.pagehide || []).forEach((fn) => fn({})),
    };
}

// ------------------------------------------------------------------ сценарии

const PORTAL_KEY = 'tradehub.scroll.sidebar';
const ADMIN_KEY = 'tradehub.scroll.admin-nav';
let checks = 0;

function check(name, fn) {
    fn();
    checks += 1;
    console.log('  ok  ' + name);
}

// 1. Прокрутка панели TradeHub запоминается.
check('portal: прокрутка сохраняется в sessionStorage', () => {
    const backing = new Map();
    const sidebar = makePanel({ attrs: { 'data-keep-scroll': 'sidebar' } });
    const page = loadPage([sidebar], backing);
    page.domReady();

    sidebar.scrollTop = 900;
    sidebar.fire('scroll');
    page.flushFrames();

    assert.strictEqual(backing.get(PORTAL_KEY), '900');
});

// 2. После перехода положение возвращается.
check('portal: положение возвращается после перехода', () => {
    const backing = new Map();
    const before = makePanel({ attrs: { 'data-keep-scroll': 'sidebar' } });
    const page1 = loadPage([before], backing);
    page1.domReady();
    before.scrollTop = 900;
    before.fire('scroll');
    page1.flushFrames();

    // новая страница: тот же пользователь, новая вкладка-сессия
    const after = makePanel({ attrs: { 'data-keep-scroll': 'sidebar' } });
    const page2 = loadPage([after], backing);
    assert.strictEqual(after.scrollTop, 0, 'до восстановления панель сверху');
    page2.domReady();
    assert.strictEqual(after.scrollTop, 900, 'прокрутка восстановлена');
});

// 3. Клик сразу после прокрутки не теряется (pagehide).
check('portal: pagehide успевает сохранить последнее положение', () => {
    const backing = new Map();
    const sidebar = makePanel({ attrs: { 'data-keep-scroll': 'sidebar' } });
    const page = loadPage([sidebar], backing);
    page.domReady();

    sidebar.scrollTop = 640;
    page.firePageHide();            // без кадра анимации
    assert.strictEqual(backing.get(PORTAL_KEY), '640');
});

// 4. Панель админки находится по id и хранится под своим ключом.
check('admin: панель по id, отдельный ключ', () => {
    const backing = new Map();
    const nav = makePanel({ id: 'nav-sidebar' });
    const page = loadPage([nav], backing);
    page.domReady();

    nav.scrollTop = 1200;
    nav.fire('scroll');
    page.flushFrames();

    assert.strictEqual(backing.get(ADMIN_KEY), '1200');
    assert.strictEqual(backing.has(PORTAL_KEY), false, 'ключи не пересекаются');
});

// 5. Обе панели на одной странице (админка со своим сайдбаром).
check('обе панели работают одновременно и не мешают друг другу', () => {
    const backing = new Map();
    const sidebar = makePanel({ attrs: { 'data-keep-scroll': 'sidebar' } });
    const nav = makePanel({ id: 'nav-sidebar' });
    const page = loadPage([sidebar, nav], backing);
    page.domReady();

    sidebar.scrollTop = 300;
    nav.scrollTop = 1100;
    sidebar.fire('scroll');
    nav.fire('scroll');
    page.flushFrames();

    assert.strictEqual(backing.get(PORTAL_KEY), '300');
    assert.strictEqual(backing.get(ADMIN_KEY), '1100');
});

// 6. Без сохранённого значения панель не трогают.
check('без сохранённого значения панель остаётся сверху', () => {
    const backing = new Map();
    const sidebar = makePanel({ attrs: { 'data-keep-scroll': 'sidebar' } });
    const page = loadPage([sidebar], backing);
    page.domReady();
    assert.strictEqual(sidebar.scrollTop, 0);
});

// 7. Возврат повторяется на load, если разметка ещё не готова.
check('возврат повторяется на load, если контент ещё не разложен', () => {
    const backing = new Map();
    backing.set(PORTAL_KEY, '900');

    // первая попытка: панель ещё «не имеет» содержимого
    const early = makePanel({
        attrs: { 'data-keep-scroll': 'sidebar' },
        scrollHeight: 800, clientHeight: 800,
    });
    const page = loadPage([early], backing);
    page.domReady();
    assert.strictEqual(early.scrollTop, 0, 'пока нечего прокручивать');

    // контент отрисовался — повтор на load должен сработать
    early.scrollHeight = 2000;
    page.fireLoad();
    assert.strictEqual(early.scrollTop, 900, 'повтор на load восстановил');
});

// 8. Плавная прокрутка не превращает возврат в анимацию.
check('на время возврата scroll-behavior принудительно auto', () => {
    const backing = new Map();
    backing.set(PORTAL_KEY, '500');

    const sidebar = makePanel({ attrs: { 'data-keep-scroll': 'sidebar' } });
    let seen = null;
    Object.defineProperty(sidebar, 'scrollTop', {
        get() {
            return this._top || 0;
        },
        set(value) {
            seen = sidebar.style.scrollBehavior;   // что было в момент записи
            this._top = value;
        },
    });

    const page = loadPage([sidebar], backing);
    page.domReady();
    assert.strictEqual(seen, 'auto', 'во время возврата прокрутка мгновенная');
    assert.strictEqual(sidebar.style.scrollBehavior, undefined,
        'после возврата прежнее значение стиля восстановлено');
});

// 9. Хранилище недоступно — страница не падает.
check('недоступное хранилище не ломает страницу', () => {
    const sidebar = makePanel({ attrs: { 'data-keep-scroll': 'sidebar' } });
    const rafQueue = [];
    const document = {
        readyState: 'loading',
        querySelectorAll: () => [sidebar],
        getElementById: () => null,
        addEventListener: () => {},
    };
    const window = {
        requestAnimationFrame: (fn) => rafQueue.push(fn),
        addEventListener: () => {},
    };
    const hostile = {
        getItem() { throw new Error('denied'); },
        setItem() { throw new Error('denied'); },
    };

    new Function('document', 'window', 'sessionStorage', CODE)(document, window, hostile);
    sidebar.scrollTop = 700;
    sidebar.fire('scroll');
    while (rafQueue.length) {
        rafQueue.shift()();
    }
    assert.strictEqual(sidebar.scrollTop, 700, 'страница продолжает работать');
});

console.log('\nвсе проверки пройдены: ' + checks);
