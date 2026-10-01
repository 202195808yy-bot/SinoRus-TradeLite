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
const vm = require('vm');

const target = process.argv[2];
const CODE = fs.readFileSync(target, 'utf8');

// ---------------------------------------------------- синтаксис как в браузере
// `vm.Script` компилирует файл как обычный скрипт и НЕ оборачивает его в
// функцию — поэтому `return` вне функции здесь падает. А `node --check`
// (обёртка CommonJS) и `new Function` такую ошибку скрывают: код «проходит
// проверку», но в браузере не выполняется ни одна строка. Именно на этом
// сломался keep-scroll.js: скрипт грузился с кодом 200 и молча ничего не
// делал. Поэтому проверка синтаксиса идёт первой и без обёртки.
try {
    new vm.Script(CODE);
    console.log('  ok  синтаксис: файл разбирается как обычный скрипт');
} catch (err) {
    console.error('  FAIL синтаксис (как в браузере): ' + err.message);
    console.error('       node --check такую ошибку не показывает — ' +
        'он оборачивает код в функцию');
    process.exit(1);
}

// ---------------------------------------------------------------- окружение

function makePanel({
    attrs = {}, id = null, scrollHeight = 2000, clientHeight = 800,
    offsetHeight = null, docTop = 100,
} = {}) {
    let top = 0;
    const listeners = {};
    const panel = {
        id,
        style: {},
        scrollHeight,
        clientHeight,
        // высота панели на странице; по умолчанию совпадает с видимой
        offsetHeight: offsetHeight === null ? clientHeight : offsetHeight,
        docTop,                     // положение панели в координатах документа
        env: { winY: 0, docHeight: 4000 },
        get scrollTop() {
            return top;
        },
        set scrollTop(value) {
            // настоящая прокрутка упирается в предел содержимого;
            // высоты читаются с самого элемента, а не из замыкания,
            // чтобы тест мог «дорастить» содержимое после первой попытки
            top = Math.max(0, Math.min(value, panel.scrollHeight - panel.clientHeight));
        },
        // координаты относительно окна: top = положение в документе
        // минус текущая прокрутка страницы
        getBoundingClientRect: () => ({ top: panel.docTop - panel.env.winY }),
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
function loadPage(panels, backing, {
    readyState = 'loading', docHeight = 4000, innerHeight = 700,
} = {}) {
    const rafQueue = [];
    const docListeners = {};
    const winListeners = {};
    // общая для панелей и окна «прокрутка страницы»
    const env = { winY: 0, docHeight: innerHeight + docHeight };

    panels.forEach((p) => {
        p.env = env;
    });

    const document = {
        readyState,
        documentElement: { style: {} },
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
        innerHeight,
        get scrollY() {
            return env.winY;
        },
        // настоящая прокрутка упирается в конец документа
        scrollTo: (x, value) => {
            env.winY = Math.max(0, Math.min(value, env.docHeight - innerHeight));
        },
        requestAnimationFrame: (fn) => rafQueue.push(fn),
        addEventListener: (type, fn) => {
            (winListeners[type] = winListeners[type] || []).push(fn);
        },
    };

    new Function('document', 'window', 'sessionStorage', CODE)(
        document, window, makeStorage(backing));

    return {
        env,
        scrollPageTo: (y) => window.scrollTo(0, y),
        flushFrames: () => {
            while (rafQueue.length) {
                rafQueue.shift()();
            }
        },
        domReady: () => (docListeners.DOMContentLoaded || []).forEach((fn) => fn({})),
        fireLoad: () => (winListeners.load || []).forEach((fn) => fn({})),
        firePageHide: () => (winListeners.pagehide || []).forEach((fn) => fn({})),
        fireWindowScroll: () => (winListeners.scroll || []).forEach((fn) => fn({})),
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
check('фронтенд: прокрутка сохраняется в sessionStorage', () => {
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
check('фронтенд: положение возвращается после перехода', () => {
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
check('фронтенд: pagehide успевает сохранить последнее положение', () => {
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

    // первая попытка: содержимое ещё «дорисовывается» — прокрутка всего 100px.
    // Панель при этом обязана оставаться прокручиваемой самой
    // (scrollHeight > clientHeight), иначе это уже режим узкого окна.
    const early = makePanel({
        attrs: { 'data-keep-scroll': 'sidebar' },
        scrollHeight: 900, clientHeight: 800,
    });
    const page = loadPage([early], backing);
    page.domReady();
    assert.strictEqual(early.scrollTop, 100, 'пока упёрлись в предел');

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

// ---------- узкое окно: панель растянута, прокручивается страница ----------
// Ниже @media (max-width: 900px) у .sidebar снимаются position: sticky и
// max-height, поэтому она перестаёт прокручиваться сама, а тянется на
// полторы тысячи пикселей перед содержимым. Тогда сохранять нужно
// прокрутку страницы.

function stacked() {
    return {
        attrs: { 'data-keep-scroll': 'sidebar' },
        scrollHeight: 1737, clientHeight: 1737,   // содержимое == высота
        offsetHeight: 1737, docTop: 100,          // панель — сразу под шапкой
    };
}

// 10. Панель не прокручивается сама — сохраняется прокрутка страницы.
check('узкое окно: сохраняется прокрутка страницы, а не панели', () => {
    const backing = new Map();
    const sidebar = makePanel(stacked());
    const page = loadPage([sidebar], backing);
    page.domReady();

    assert.strictEqual(sidebar.scrollTop, 0, 'панель сама не прокручивается');
    page.scrollPageTo(900);
    page.fireWindowScroll();
    page.flushFrames();

    assert.strictEqual(backing.get(PORTAL_KEY), '900');
});

// 11. После перехода прокрутка страницы возвращается.
check('узкое окно: прокрутка страницы возвращается после перехода', () => {
    const backing = new Map();
    const before = makePanel(stacked());
    const page1 = loadPage([before], backing);
    page1.domReady();
    page1.scrollPageTo(900);
    page1.fireWindowScroll();
    page1.flushFrames();

    const after = makePanel(stacked());
    const page2 = loadPage([after], backing);
    assert.strictEqual(page2.env.winY, 0, 'новая страница открылась сверху');
    page2.domReady();
    assert.strictEqual(page2.env.winY, 900, 'прокрутка страницы восстановлена');
});

// 12. Ушли, читая содержимое, — к панели читателя не возвращаем.
check('узкое окно: ушли из содержимого — к панели не возвращаем', () => {
    const backing = new Map();
    const before = makePanel(stacked());
    const page1 = loadPage([before], backing);
    page1.domReady();
    page1.scrollPageTo(2600);           // панель заканчивается на 100 + 1737
    page1.fireWindowScroll();
    page1.flushFrames();
    assert.strictEqual(backing.get(PORTAL_KEY), '2600');

    const after = makePanel(stacked());
    const page2 = loadPage([after], backing);
    page2.domReady();
    assert.strictEqual(page2.env.winY, 0,
        'страница сверху: это был переход из содержимого');
});

// 13. Документ короче сохранённого положения — страница не ломается.
check('узкое окно: документ короче — возврат просто упирается в конец', () => {
    const backing = new Map();
    // 1500 — внутри панели (100…1837), то есть возврат полагается,
    // но документ короче и прокрутка упирается в конец
    backing.set(PORTAL_KEY, '1500');

    const sidebar = makePanel(stacked());
    const page = loadPage([sidebar], backing, { docHeight: 400 });
    page.domReady();
    page.fireLoad();
    assert.strictEqual(page.env.winY, 400, 'уперлись в конец документа');
});

console.log('\nвсе проверки пройдены: ' + checks);
