'use strict';
/* 在页面跳转之间保持侧边导航的滚动位置。
 *
 * TradeHub 的侧栏与管理后台的分区面板是独立的
 * 可滚动区域（``overflow: auto``）。浏览器只恢复
 * 窗口本身的滚动，因此跳转后面板会回滚
 * 到第一个条目：想回到所需的模块，只能
 * 重新滚动面板。
 *
 * 还有第二种情况，而且并不明显。在窄窗口下
 * （``@media (max-width: 900px)``）面板会被拉伸 —
 * ``position: static; max-height: none`` — 从而不再
 * 自行滚动：滚动的是整个页面，面板在内容之前
 * 拉长到一千五百像素。此时要保存的不是面板的 ``scrollTop``
 * 而是窗口的滚动 — 否则跳转照样会把它
 * 抛回顶部。两种情况当场可以区分：面板自行滚动
 * 当且仅当内容比它高。
 *
 * 值保存在 ``sessionStorage`` 中（按标签页 — 与
 * Django 在管理面板中保存过滤器的方式完全相同）。
 *
 * 标记：元素用 ``data-keep-scroll="<ключ>"`` 属性标注。
 * 管理后台的侧栏由 Django 生成，没有该属性，因此
 * 通过 ``id`` 查找。
 *
 * 全部代码都放在一个立即调用的函数里。这不是风格，而是
 * 必要：``return`` 不能出现在普通脚本的函数之外，
 * 否则整个文件在浏览器中不会执行（``node --check``
 * 不会报出这种错误 — 它会把文件包装成函数）。
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
            return null;              // 隐私模式：禁止使用存储
        }
    }

    function write(key, value) {
        try {
            sessionStorage.setItem(key, String(value));
        } catch (err) {
            /* 存储不可用 — 就不保存位置 */
        }
    }

    /** 只有当内容比面板高时，面板才会自行滚动。 */
    function scrollsItself(el) {
        return el.scrollHeight > el.clientHeight + 1;
    }

    /** 导航当前位于何处：面板内还是页面上。 */
    function positionOf(el) {
        return scrollsItself(el) ? el.scrollTop : window.scrollY;
    }

    function applyPosition(el, top) {
        if (scrollsItself(el)) {
            // 平滑滚动会把恢复位置变成每次页面加载时的
            // 动画，因此在恢复期间要将其
            // 暂时关闭。
            const previous = el.style.scrollBehavior;
            el.style.scrollBehavior = 'auto';
            el.scrollTop = top;
            el.style.scrollBehavior = previous;
            return el.scrollTop >= top - 1;
        }

        // 面板被拉伸：需要恢复的是页面滚动。但只有
        // 在离开时能看到导航的情况下才恢复 — 否则这是从
        // 内容区发起的跳转，无需把读者带回面板。
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

    // 面板和页面都可能被滚动 — 两者都监听。
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

    // 离开页面前最后一次机会：点击可能在
    // 滚动之后立即发生，早于 requestAnimationFrame 触发。
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
                pending = true;       // 内容尚未排布完成
            }
        });
        settled = !pending;
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', restoreAll);
    } else {
        restoreAll();
    }
    // 第二次执行 — 在完全加载之后：面板高度通过
    // calc(100vh …) 设定，到这时已最终计算完成。
    // 仅当第一次恢复失败时才会重复执行。
    window.addEventListener('load', restoreAll);
})();

