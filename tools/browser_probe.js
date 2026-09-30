/* Проверка страниц в настоящем браузере через Chrome DevTools Protocol.
 *
 * Зачем: песочница убивает Playwright (Chromium стартует и получает
 * SIGTERM без вывода), а системный Chrome в headless-режиме работает.
 * Управляем им напрямую по CDP — Node 22 даёт глобальные WebSocket и
 * fetch, внешних зависимостей не нужно.
 *
 * Зачем именно браузер: `node --check` оборачивает файл в функцию
 * CommonJS и потому НЕ видит, например, `return` вне функции, из-за
 * которого скрипт не выполняется в браузере целиком. Такая ошибка
 * проходит все статические проверки и видна только здесь.
 *
 * Требуется запущенный сервер разработки:
 *     python manage.py runserver 127.0.0.1:8731
 *     node tools/browser_probe.js http://127.0.0.1:8731 [логин] [пароль]
 *
 * Путь к Chrome можно задать переменной окружения CHROME.
 */
'use strict';
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const CANDIDATES = [
    process.env.CHROME,
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
    '/usr/bin/google-chrome',
    '/usr/bin/chromium',
].filter(Boolean);

const CHROME = CANDIDATES.find((p) => {
    try {
        return fs.statSync(p).isFile();
    } catch (err) {
        return false;
    }
});

const PORT = Number(process.env.CDP_PORT || 9333);
const BASE = (process.argv[2] || 'http://127.0.0.1:8731').replace(/\/$/, '');
const USER = process.argv[3] || 'admin';
const PASS = process.argv[4] || 'Waxx2003';

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

class Cdp {
    constructor(ws) {
        this.ws = ws;
        this.seq = 0;
        this.pending = new Map();
        this.handlers = [];
        this.exceptions = [];
        this.consoleErrors = [];
        ws.onmessage = (ev) => {
            const msg = JSON.parse(ev.data);
            if (msg.id && this.pending.has(msg.id)) {
                const { resolve, reject } = this.pending.get(msg.id);
                this.pending.delete(msg.id);
                if (msg.error) {
                    reject(new Error(JSON.stringify(msg.error)));
                } else {
                    resolve(msg.result);
                }
                return;
            }
            if (msg.method === 'Runtime.exceptionThrown') {
                const d = msg.params.exceptionDetails;
                this.exceptions.push(
                    d.text + ' ' + ((d.exception || {}).description || ''));
            }
            if (msg.method === 'Runtime.consoleAPICalled' && msg.params.type === 'error') {
                this.consoleErrors.push(
                    msg.params.args.map((a) => a.value || a.description).join(' '));
            }
            this.handlers.slice().forEach((h) => h(msg));
        };
    }

    static async connect(wsUrl) {
        const ws = new WebSocket(wsUrl);
        await new Promise((resolve, reject) => {
            ws.onopen = resolve;
            ws.onerror = () => reject(new Error('WebSocket: не подключиться'));
        });
        return new Cdp(ws);
    }

    send(method, params = {}) {
        const id = ++this.seq;
        this.ws.send(JSON.stringify({ id, method, params }));
        return new Promise((resolve, reject) => this.pending.set(id, { resolve, reject }));
    }

    once(method, timeout = 20000) {
        return new Promise((resolve, reject) => {
            const timer = setTimeout(
                () => reject(new Error('таймаут: ' + method)), timeout);
            const handler = (msg) => {
                if (msg.method !== method) {
                    return;
                }
                clearTimeout(timer);
                this.handlers = this.handlers.filter((h) => h !== handler);
                resolve(msg.params);
            };
            this.handlers.push(handler);
        });
    }

    async eval(expression) {
        const r = await this.send('Runtime.evaluate', {
            expression, returnByValue: true, awaitPromise: true,
        });
        if (r.exceptionDetails) {
            throw new Error('ошибка JS: ' + JSON.stringify(r.exceptionDetails));
        }
        return r.result.value;
    }

    async navigate(url) {
        const loaded = this.once('Page.loadEventFired');
        await this.send('Page.navigate', { url });
        await loaded;
        await sleep(500);        // отложенные скрипты + requestAnimationFrame
    }
}

async function targetUrl() {
    for (let i = 0; i < 80; i += 1) {
        try {
            const res = await fetch(`http://127.0.0.1:${PORT}/json/list`);
            const page = (await res.json()).find((t) => t.type === 'page');
            if (page) {
                return page.webSocketDebuggerUrl;
            }
        } catch (err) {
            /* Chrome ещё поднимается */
        }
        await sleep(250);
    }
    throw new Error('Chrome не запустился');
}

const STATE = (sel, key) => `(() => {
  const sb = document.querySelector(${JSON.stringify(sel)});
  if (!sb) return {found: false};
  return {
    found: true,
    scrollTop: sb.scrollTop,
    scrollHeight: sb.scrollHeight,
    clientHeight: sb.clientHeight,
    scrollable: sb.scrollHeight > sb.clientHeight,
    overflowY: getComputedStyle(sb).overflowY,
    stored: sessionStorage.getItem(${JSON.stringify(key)}),
  };
})()`;

/** Прокрутить панель, дождаться записи, перейти, прочитать состояние. */
async function scrollScenario(cdp, { from, to, sel, key }) {
    await cdp.navigate(from);
    const before = await cdp.eval(STATE(sel, key));
    await cdp.eval(`(() => {
        const sb = document.querySelector(${JSON.stringify(sel)});
        sb.scrollTop = 500;
        return sb.scrollTop;
    })()`);
    await sleep(700);
    const stored = await cdp.eval(`sessionStorage.getItem(${JSON.stringify(key)})`);
    await cdp.navigate(to);
    const after = await cdp.eval(STATE(sel, key));
    return { before, storedAfterScroll: stored, after };
}

function verdict(name, result) {
    const ok = result.storedAfterScroll === '500'
        && result.after.scrollTop === 500
        && result.before.scrollable === true;
    console.log(
        (ok ? '  ok  ' : '  FAIL') + ' ' + name
        + ': прокручиваемость=' + result.before.scrollable
        + ', записано=' + JSON.stringify(result.storedAfterScroll)
        + ', после перехода=' + result.after.scrollTop);
    return ok;
}

async function main() {
    if (!CHROME) {
        console.error('Chrome не найден. Задайте путь: CHROME=... node tools/browser_probe.js');
        process.exit(2);
    }
    const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'cdp-'));
    const chrome = spawn(CHROME, [
        '--headless=new', '--disable-gpu', '--no-sandbox',
        '--no-first-run', '--no-default-browser-check',
        '--window-size=1280,900',
        `--remote-debugging-port=${PORT}`,
        `--user-data-dir=${profile}`,
        'about:blank',
    ], { stdio: 'ignore' });

    let allOk = true;
    try {
        const cdp = await Cdp.connect(await targetUrl());
        await cdp.send('Page.enable');
        await cdp.send('Runtime.enable');

        console.log('TradeHub:');
        allOk = verdict('прокрутка боковой панели', await scrollScenario(cdp, {
            from: `${BASE}/orders/`,
            to: `${BASE}/dashboard/`,
            sel: '[data-keep-scroll]',
            key: 'tradehub.scroll.sidebar',
        })) && allOk;

        await cdp.navigate(`${BASE}/admin/login/`);
        const loginLoaded = cdp.once('Page.loadEventFired');
        await cdp.eval(`(() => {
            document.querySelector('#id_username').value = ${JSON.stringify(USER)};
            document.querySelector('#id_password').value = ${JSON.stringify(PASS)};
            document.querySelector('#login-form').submit();
            return true;
        })()`);
        await loginLoaded;
        await sleep(600);

        const loggedIn = await cdp.eval(
            `!document.body.className.includes('login')`);
        if (loggedIn) {
            console.log('Панель админки:');
            allOk = verdict('прокрутка панели разделов', await scrollScenario(cdp, {
                from: `${BASE}/admin/portal/order/`,
                to: `${BASE}/admin/portal/good/`,
                sel: '#nav-sidebar',
                key: 'tradehub.scroll.admin-nav',
            })) && allOk;
        } else {
            console.log('  --  панель админки пропущена: вход не выполнен '
                + '(передайте логин и пароль аргументами)');
        }

        if (cdp.exceptions.length || cdp.consoleErrors.length) {
            allOk = false;
            console.log('\nОшибки в браузере:');
            cdp.exceptions.forEach((e) => console.log('  exception: ' + e));
            cdp.consoleErrors.forEach((e) => console.log('  console.error: ' + e));
        } else {
            console.log('\nОшибок в консоли нет.');
        }
    } finally {
        chrome.kill();
    }

    console.log(allOk ? '\nПРОВЕРКА В БРАУЗЕРЕ ПРОЙДЕНА.' : '\nПРОВЕРКА НЕ ПРОЙДЕНА.');
    process.exit(allOk ? 0 : 1);
}

main().catch((err) => {
    console.error('СБОЙ: ' + err.message);
    process.exit(1);
});
