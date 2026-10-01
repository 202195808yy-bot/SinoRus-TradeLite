# -*- coding: utf-8 -*-
"""页面数据提供器：区块构造器与注册表。

阶段 4（“应用页面模板”）。**构造器与工具在本模块**，
具体页面的提供器分散在各应用的 ``<app>/datasets.py`` 里，
由各应用 ``AppConfig.ready()`` 通过 ``register_providers()``
登记进来。视图 ``core.views._page()`` 取到区块后交给模板
``templates/portal/page.html``。

上下文区块：

* ``kpi``    —— 汇总指标磁贴；
* ``table``  —— 表格：列 + 由 ``c()`` 单元格组成的行；
* ``fields`` —— “字段—值”卡片；
* ``list``   —— 带标签的紧凑列表。

数据模式：若用户未通过认证，与企业绑定的页面会以演示模式
显示第一个企业的数据（``mode = "demo"``）。按角色的访问约束属于
阶段 5“应用用户”。
"""

from decimal import Decimal

from django.db.models import Avg, Count, Max, Q, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone


LIST_LIMIT = 50

STATUS_TONE = {
    "draft": "muted", "new": "info", "pending": "warn", "sent": "info",
    "quoted": "info", "in_progress": "warn", "verifying": "warn",
    "issued": "info", "partial": "warn", "confirmed": "ok",
    "accepted": "ok", "active": "ok", "done": "ok", "passed": "ok",
    "provided": "ok", "checked": "ok", "paid": "ok", "resolved": "ok",
    "completed": "ok", "signed": "ok", "uploaded": "ok", "acked": "ok",
    "shipped": "info", "in_production": "info", "closed": "muted",
    "archived": "muted", "canceled": "muted", "skipped": "muted",
    "rejected": "danger", "failed": "danger", "expired": "danger",
    "blocked": "danger", "disputed": "danger", "revoked": "danger",
    "issues": "warn", "missing": "warn", "registered": "warn",
    "critical": "danger", "high": "warn", "medium": "warn", "low": "muted",
    "normal": "info",
}


# --------------------------------------------------------------- 单元格

def c(text, url=None, badge=None, mono=False, label=None):
    """表格单元格。

    ``label`` 标记单元格文本中的前缀标签，例如
    “订单 ORD-2026-0001”：``i18n.translate_cell()`` 只翻译
    标签部分（“订单 ORD-2026-0001”），编号保持原样。若没有
    该标记，这一行会被视为数据而不翻译。
    """
    cell = {"text": "" if text is None else str(text), "url": url,
            "badge": badge, "mono": mono}
    if label:
        cell["label"] = label
    return cell


def badge_of(value, label=None):
    """状态单元格，按取值挑选颜色。"""
    return {"text": label if label is not None else str(value),
            "url": None, "badge": STATUS_TONE.get(str(value), "muted"),
            "mono": False}


def tbl(title, columns, rows, empty="Данных пока нет", note=None):
    return {"kind": "table", "title": title, "columns": columns,
            "rows": rows[:LIST_LIMIT], "empty": empty, "note": note,
            "truncated": len(rows) > LIST_LIMIT}


def fld(title, items):
    return {"kind": "fields", "title": title,
            "items": [[k, "" if v is None else str(v)] for k, v in items]}


def kpi(title, items):
    return {"kind": "kpi", "title": title, "items": items}


def k(label, value, hint=None, tone=""):
    return {"label": label, "value": value, "hint": hint, "tone": tone}


def lst(title, items, empty="Данных пока нет"):
    return {"kind": "list", "title": title, "items": items, "empty": empty}


def url_for(name, *args):
    """注册表页面的反向地址（不查询 urlconf）。"""
    from .pages import PAGE_BY_NAME
    path = PAGE_BY_NAME[name]["path"]
    if args:
        return "/" + path.replace("<int:pk>", str(args[0]))
    return "/" + path


# --------------------------------------------------------------- 工具函数

def money(value, symbol="", places=2):
    if value is None:
        return "—"
    q = Decimal(value).quantize(Decimal("0.01" if places == 2 else "0.1"))
    txt = f"{q:,.{places}f}".replace(",", " ").replace(".", ",")
    return f"{txt} {symbol}".strip()


def num(value, places=0):
    if value is None:
        return "—"
    if places:
        return f"{Decimal(value):.{places}f}".replace(".", ",")
    return str(int(value))


def dt(value):
    return value.strftime("%d.%m.%Y") if value else "—"


def dtm(value):
    return timezone.localtime(value).strftime("%d.%m.%Y %H:%M") if value else "—"


def safe(obj, attr, default="—"):
    """不抛异常地获取关联对象的值（OneToOne 反向关联）。"""
    try:
        value = getattr(obj, attr)
    except Exception:                                     # noqa: BLE001
        return default
    return default if value is None else value


def current_enterprise(request):
    """用户的企业；演示模式下取数据库中的第一个。"""
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        from accounts.models import Membership
        member = (Membership.objects
                  .filter(user=user, is_active=True)
                  .select_related("enterprise").first())
        if member:
            return member.enterprise, False
    from accounts.models import Enterprise
    return Enterprise.objects.first(), True


def demo_mode(demo):
    return "demo" if demo else None


def q_param(request, key, default=""):
    return (request.GET.get(key) or default).strip()


# ======================================================================
# M0. 通用页面
# ======================================================================

def index_data(request, **kw):
    """主页：平台概览与最新订单。

    这是唯一的跨领域聚合页，因此模型在**函数内**导入：
    内核不反向依赖具体领域应用，主页只是把各应用的
    数字汇总到一处。
    """
    from accounts.models import Enterprise
    from catalog.models import Good
    from tasks.models import Task
    from trading.models import Order

    orders = Order.objects.all()
    blocks = [
        kpi("Сводка платформы", [
            k("Предприятия", Enterprise.objects.count(),
              "участники области"),
            k("Товары", Good.objects.count(), "в каталоге"),
            k("Заказы", orders.count(), "заключено"),
            k("Задачи в работе", Task.objects.filter(
                status__in=["new", "in_progress"]).count(), "открыто"),
        ]),
        tbl("Последние заказы",
            ["Номер", "Покупатель", "Поставщик", "Сумма", "Статус"],
            [[c(o.number, url_for("order_detail", o.pk), mono=True),
              c(o.buyer.name_ru),
              c(o.supplier.name_ru),
              c(money(o.amount, safe(o.currency, "symbol", ""))),
              badge_of(o.status, o.get_status_display())]
             for o in orders.select_related(
                 "buyer", "supplier", "currency")[:10]],
            empty="Заказы ещё не заключены"),
    ]
    return {"blocks": blocks}


# ======================================================================
# 提供器注册表
# ======================================================================

#: 页面名 -> 提供器函数。各应用在 ``ready()`` 里填充。
PAGE_DATA = {}


def register_providers(mapping):
    """登记一个应用的提供器。重复登记以最后一次为准。"""
    PAGE_DATA.update(mapping)
    return len(mapping)


def provider_for(name):
    """页面数据提供器，或 None（页面保持为原型）。"""
    return PAGE_DATA.get(name)


def coverage():
    """（带数据的页面、原型页面）——供 tools/check_data.py 使用。"""
    from core.pages import PAGES
    wired = [p["name"] for p in PAGES if p["name"] in PAGE_DATA]
    proto = [p["name"] for p in PAGES if p["name"] not in PAGE_DATA]
    return wired, proto


#: 主页由内核自己提供——它是跨领域聚合页，
#: 不属于任何单一应用。
PAGE_DATA["index"] = index_data
