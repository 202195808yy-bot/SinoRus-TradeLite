# -*- coding: utf-8 -*-
"""Данные страниц приложения: провайдеры контекста для представлений.

Этап 4 («Шаблоны страниц приложения»). Модуль связывает имя страницы из
реестра ``portal/pages.py`` с функцией, собирающей данные из моделей
``portal/models.py``. Представление ``portal.views._page()`` вызывает
провайдер и передаёт блоки в шаблон ``portal/page.html``.

Архитектура повторяет реестр страниц: один источник данных о том, какая
страница какие данные показывает. Страницы без провайдера остаются
прототипами (см. ``coverage()``).

Блоки контекста:

* ``kpi``    — плитки сводных показателей;
* ``table``  — таблица: колонки + строки из ячеек ``cell()``;
* ``fields`` — карточка «поле — значение»;
* ``list``   — компактный список с подписями.

Режим данных: если пользователь не аутентифицирован, страницы, привязанные
к предприятию, показывают данные первого предприятия в режиме
демонстрации (``mode = "demo"``). Ограничение доступа по ролям —
этап 5 «Пользователи приложения».
"""

from decimal import Decimal

from django.db.models import Avg, Count, Max, Q, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone

from . import models as m

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


# --------------------------------------------------------------- ячейки

def c(text, url=None, badge=None, mono=False, label=None):
    """Ячейка таблицы.

    ``label`` помечает подпись-префикс внутри текста ячейки, например
    «Заказ ORD-2026-0001»: ``i18n.translate_cell()`` переведёт только
    подпись («订单 ORD-2026-0001»), а номер оставит как есть. Без этой
    пометки строка считалась бы данными и не переводилась.
    """
    cell = {"text": "" if text is None else str(text), "url": url,
            "badge": badge, "mono": mono}
    if label:
        cell["label"] = label
    return cell


def badge_of(value, label=None):
    """Ячейка-статус с подбором цвета по значению."""
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
    """Обратный адрес страницы реестра (без обращения к urlconf)."""
    from .pages import PAGE_BY_NAME
    path = PAGE_BY_NAME[name]["path"]
    if args:
        return "/" + path.replace("<int:pk>", str(args[0]))
    return "/" + path


# --------------------------------------------------------------- утилиты

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
    """Значение связанного объекта без исключений (обратные OneToOne)."""
    try:
        value = getattr(obj, attr)
    except Exception:                                     # noqa: BLE001
        return default
    return default if value is None else value


def current_enterprise(request):
    """Предприятие пользователя; в демо-режиме — первое в базе."""
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        member = (m.Membership.objects
                  .filter(user=user, is_active=True)
                  .select_related("enterprise").first())
        if member:
            return member.enterprise, False
    return m.Enterprise.objects.first(), True


def _mode(demo):
    return "demo" if demo else None


def _q(request, key, default=""):
    return (request.GET.get(key) or default).strip()


# ======================================================================
# M0. Общие страницы
# ======================================================================

def index_data(request, **kw):
    orders = m.Order.objects.all()
    blocks = [
        kpi("Сводка платформы", [
            k("Предприятия", m.Enterprise.objects.count(),
              "участники области"),
            k("Товары", m.Good.objects.count(), "в каталоге"),
            k("Заказы", orders.count(), "заключено"),
            k("Задачи в работе", m.Task.objects.filter(
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
# M1. Предприятие и аккаунт
# ======================================================================

def enterprise_profile_data(request, **kw):
    ent, demo = current_enterprise(request)
    if ent is None:
        return {"blocks": [], "mode": "demo"}
    member = m.Membership.objects.filter(
        enterprise=ent, user=request.user).first() \
        if request.user.is_authenticated else None
    blocks = [
        fld("Реквизиты предприятия", [
            ("Наименование (рус.)", ent.name_ru),
            ("Наименование (кит.)", ent.name_zh or "—"),
            ("Страна", safe(ent, "country")),
            ("Отрасль", safe(ent, "industry")),
            ("ИНН / код", ent.tin or "—"),
            ("Адрес", ent.address or "—"),
            ("Банковский счёт", ent.bank_account or "—"),
            ("Статус", ent.get_status_display()),
        ]),
        kpi("Активность", [
            k("Членство", m.Membership.objects.filter(
                enterprise=ent, is_active=True).count(), "сотрудников"),
            k("Контрагенты", m.Counterparty.objects.filter(
                enterprise=ent).count(), "в справочнике"),
            k("Заказы", m.Order.objects.filter(
                Q(buyer=ent) | Q(supplier=ent)).count(), "всего"),
            k("Приглашения", m.Invitation.objects.filter(
                enterprise=ent, status="pending").count(), "ожидают"),
        ]),
    ]
    if member:
        blocks.insert(0, fld("Текущая роль", [
            ("Пользователь", request.user.get_username()),
            ("Роль", member.get_role_display()),
            ("Подразделение", member.department or "—"),
            ("В членстве с", dt(member.joined_at)),
        ]))
    blocks.append(tbl("Контрагенты",
                      ["Наименование", "Контакт", "Телефон", "Базис"],
                      [[c(cp.name), c(cp.contact_person or "—"),
                        c(cp.phone or "—"),
                        c(cp.get_incoterm_display() or "—")]
                       for cp in m.Counterparty.objects.filter(
                           enterprise=ent)[:20]],
                      empty="Контрагенты не заведены"))
    return {"blocks": blocks, "mode": _mode(demo)}


def enterprise_verification_data(request, **kw):
    ent, demo = current_enterprise(request)
    if ent is None:
        return {"blocks": [], "mode": "demo"}
    docs = (m.Document.objects
            .filter(Q(order__buyer=ent) | Q(order__supplier=ent))
            .select_related("doc_type", "order"))
    certs = m.Certificate.objects.all()
    blocks = [
        kpi("Состояние проверки", [
            k("Статус предприятия", ent.get_status_display(),
              tone="ok" if ent.status == "active" else "warn"),
            k("Документы", docs.count(), "загружено"),
            k("Сертификаты", certs.count(), "по товарам"),
            k("Истекают ≤ 30 дней", certs.filter(
                valid_until__lte=timezone.now().date() +
                timezone.timedelta(days=30)).count(), tone="warn"),
        ]),
        tbl("Документы предприятия",
            ["Тип", "Заказ", "Выдан", "Действителен до", "Статус"],
            [[c(safe(d.doc_type, "name_ru")),
              c(safe(d.order, "number")),
              c(dt(d.issued_date)), c(dt(d.valid_until)),
              badge_of(d.status, d.get_status_display())]
             for d in docs[:20]],
            empty="Документы не загружены"),
        tbl("Сертификаты соответствия",
            ["Номер", "Вид", "Товар", "Действителен до", "ФГИС"],
            [[c(cert.number, mono=True),
              c(cert.get_kind_display()),
              c(safe(cert.good, "name_ru")),
              c(dt(cert.valid_until)),
              c(cert.fgis_no or "—")]
             for cert in certs.select_related("good")[:20]],
            empty="Сертификаты не загружены"),
    ]
    return {"blocks": blocks, "mode": _mode(demo)}


def enterprise_members_data(request, **kw):
    ent, demo = current_enterprise(request)
    qs = m.Membership.objects.select_related("user", "enterprise")
    if ent is not None:
        qs = qs.filter(enterprise=ent)
    blocks = [
        tbl("Сотрудники и роли",
            ["Пользователь", "Роль", "Подразделение", "С нами с", "Активен"],
            [[c(mem.user.get_username()),
              badge_of(mem.role, mem.get_role_display()),
              c(mem.department or "—"), c(dt(mem.joined_at)),
              c("да" if mem.is_active else "нет")]
             for mem in qs],
            empty="Сотрудники не заведены"),
    ]
    return {"blocks": blocks, "mode": _mode(demo)}


def enterprise_invitations_data(request, **kw):
    ent, demo = current_enterprise(request)
    qs = m.Invitation.objects.select_related("enterprise", "invited_by")
    if ent is not None:
        qs = qs.filter(enterprise=ent)
    blocks = [
        tbl("Приглашения партнёров",
            ["Код", "Электронная почта", "Роль", "Действует до", "Статус"],
            [[c(inv.code, mono=True), c(inv.email),
              c(inv.get_role_display()), c(dt(inv.valid_until)),
              badge_of(inv.status, inv.get_status_display())]
             for inv in qs],
            empty="Приглашений нет"),
    ]
    return {"blocks": blocks, "mode": _mode(demo)}


# ======================================================================
# M2. Товары
# ======================================================================

def goods_list_data(request, **kw):
    qs = (m.Good.objects
          .select_related("category", "uom", "category__parent"))
    q, cat, active = _q(request, "q"), _q(request, "category"), _q(request, "active")
    if q:
        qs = qs.filter(Q(name_ru__icontains=q) | Q(name_zh__icontains=q)
                       | Q(sku__icontains=q) | Q(brand__icontains=q))
    if cat:
        qs = qs.filter(Q(category__code=cat) | Q(category__parent__code=cat))
    if active in ("1", "0"):
        qs = qs.filter(is_active=(active == "1"))
    blocks = [
        kpi("Каталог", [
            k("Товаров", m.Good.objects.count(), "всего"),
            k("Активных", m.Good.objects.filter(is_active=True).count()),
            k("Категорий", m.GoodCategory.objects.count()),
            k("Упаковок", m.Packaging.objects.count(), "описано"),
        ]),
        tbl("Товары",
            ["Артикул", "Наименование", "Наименование (кит.)", "Категория",
             "Единица", "Активен"],
            [[c(g.sku, url_for("goods_detail", g.pk), mono=True),
              c(g.name_ru), c(g.name_zh or "—"),
              c(safe(g.category, "name_ru")),
              c(safe(g.uom, "code")),
              c("да" if g.is_active else "нет")]
             for g in qs],
            empty="Товары не найдены",
            note=("Отбор: поиск «%s»" % q) if q else None),
    ]
    return {"blocks": blocks}


def goods_detail_data(request, pk, **kw):
    g = get_object_or_404(
        m.Good.objects.select_related("category", "uom"), pk=pk)
    attrs = g.attributes or {}
    blocks = [
        fld("Карточка товара", [
            ("Артикул (SKU)", g.sku),
            ("Код ТН ВЭД", g.hs_code or "—"),
            ("Наименование (рус.)", g.name_ru),
            ("Наименование (кит.)", g.name_zh or "—"),
            ("Категория", safe(g.category, "name_ru")),
            ("Единица измерения", safe(g.uom, "name_ru")),
            ("Торговая марка", g.brand or "—"),
            ("Срок хранения, сут", g.shelf_life_days or "—"),
            ("В каталоге", "да" if g.is_active else "нет"),
            ("Создан", dt(g.created_at)),
        ]),
        fld("Характеристики", list(attrs.items()) or [("—", "не заполнены")]),
        tbl("Упаковка",
            ["Вид", "Штук в упаковке", "Вес, кг", "Габариты"],
            [[c(p.get_kind_display()), c(num(p.units_per_pack)),
              c(num(p.unit_weight_kg, 3)), c(p.dims or "—")]
             for p in g.packagings.all()],
            empty="Упаковка не описана"),
        tbl("Изображения",
            ["Файл", "Порядок", "Главное"],
            [[c(im.file.name or "—"), c(num(im.order)),
              c("да" if im.is_main else "нет")]
             for im in g.images.all()],
            empty="Изображений нет"),
        tbl("Сертификаты товара",
            ["Номер", "Вид", "Действителен до", "Осталось дней"],
            [[c(cert.number, mono=True), c(cert.get_kind_display()),
              c(dt(cert.valid_until)),
              c(cert.days_to_expiry)]
             for cert in g.certificates.all()],
            empty="Сертификаты не заведены"),
    ]
    return {"blocks": blocks}


def goods_form_data(request, **kw):
    blocks = [
        tbl("Справочник категорий",
            ["Код", "Наименование", "Уровень", "Родительская категория"],
            [[c(cat.code, mono=True), c(cat.name_ru), c(num(cat.level)),
              c(safe(cat.parent, "name_ru"))]
             for cat in m.GoodCategory.objects.select_related("parent")],
            empty="Категории не заведены"),
        tbl("Единицы измерения",
            ["Код", "Наименование", "Вид"],
            [[c(u.code, mono=True), c(u.name_ru), c(u.get_kind_display())]
             for u in m.Uom.objects.all()],
            empty="Единицы не заведены"),
    ]
    return {"blocks": blocks}


# ======================================================================
# M3. Запросы и предложения
# ======================================================================

def rfq_list_data(request, **kw):
    qs = (m.Rfq.objects
          .select_related("buyer", "currency")
          .annotate(n_lines=Count("lines")))
    status = _q(request, "status")
    if status:
        qs = qs.filter(status=status)
    blocks = [
        kpi("Запросы", [
            k("Всего", m.Rfq.objects.count()),
            k("Ожидают ответа", m.Rfq.objects.filter(
                status="sent").count(), tone="warn"),
            k("С предложениями", m.Rfq.objects.filter(
                status="quoted").count()),
            k("Позиций", m.RfqLine.objects.count(), "всего"),
        ]),
        tbl("Список запросов",
            ["Номер", "Наименование", "Покупатель", "Срок ответа",
             "Базис", "Валюта", "Позиций", "Статус"],
            [[c(r.number, url_for("rfq_detail", r.pk), mono=True),
              c(r.title), c(r.buyer.name_ru), c(dt(r.due_date)),
              c(r.get_incoterm_display()),
              c(safe(r.currency, "code")), c(num(r.n_lines)),
              badge_of(r.status, r.get_status_display())]
             for r in qs],
            empty="Запросы не созданы"),
    ]
    return {"blocks": blocks}


def rfq_create_data(request, **kw):
    blocks = [
        tbl("Товары для позиций запроса",
            ["Артикул", "Наименование", "Единица", "Срок хранения, сут"],
            [[c(g.sku, url_for("goods_detail", g.pk), mono=True),
              c(g.name_ru), c(safe(g.uom, "code")),
              c(g.shelf_life_days or "—")]
             for g in m.Good.objects.filter(
                 is_active=True).select_related("uom")],
            empty="Сначала заведите товары"),
        tbl("Валюты расчётов",
            ["Код", "Наименование", "Символ", "Знаков"],
            [[c(cur.code, mono=True), c(cur.name_ru), c(cur.symbol),
              c(num(cur.decimals))]
             for cur in m.Currency.objects.all()],
            empty="Валюты не заведены"),
    ]
    return {"blocks": blocks}


def rfq_detail_data(request, pk, **kw):
    r = get_object_or_404(
        m.Rfq.objects.select_related("buyer", "currency"), pk=pk)
    lines = r.lines.select_related("good")
    quotes = r.quotes.select_related("supplier", "currency")
    blocks = [
        fld("Карточка запроса", [
            ("Номер", r.number),
            ("Наименование", r.title),
            ("Покупатель", r.buyer.name_ru),
            ("Срок ответа", dt(r.due_date)),
            ("Базис поставки", r.get_incoterm_display()),
            ("Валюта", safe(r.currency, "code")),
            ("Статус", r.get_status_display()),
            ("Создан", dt(r.created_at)),
            ("Комментарий", r.comment or "—"),
        ]),
        tbl("Позиции запроса",
            ["Товар", "Количество", "Целевая цена", "Требование"],
            [[c(safe(line.good, "name_ru")), c(num(line.qty, 3)),
              c(money(line.target_price)), c(line.requirement or "—")]
             for line in lines],
            empty="Позиции не заполнены"),
        tbl("Полученные предложения",
            ["Номер", "Поставщик", "Сумма", "Действует до", "Статус"],
            [[c(q.number, url_for("quote_detail", q.pk), mono=True),
              c(q.supplier.name_ru),
              c(money(q.amount, safe(q.currency, "symbol", ""))),
              c(dt(q.valid_until)),
              badge_of(q.status, q.get_status_display())]
             for q in quotes],
            empty="Предложения ещё не получены"),
    ]
    return {"blocks": blocks}


def quote_list_data(request, **kw):
    qs = (m.Quote.objects
          .select_related("supplier", "currency", "rfq")
          .annotate(n_lines=Count("lines", distinct=True),
                    last_version=Max("versions__version")))
    status = _q(request, "status")
    if status:
        qs = qs.filter(status=status)
    blocks = [
        kpi("Предложения", [
            k("Всего", m.Quote.objects.count()),
            k("Действующих", m.Quote.objects.filter(
                status="sent").count(), "ожидают решения"),
            k("Принятых", m.Quote.objects.filter(status="accepted").count(),
              tone="ok"),
            k("Версий", m.QuoteVersion.objects.count(), "изменений"),
        ]),
        tbl("Список предложений",
            ["Номер", "Запрос", "Поставщик", "Сумма", "Действует до",
             "Версия", "Статус"],
            [[c(q.number, url_for("quote_detail", q.pk), mono=True),
              c(safe(q.rfq, "number")), c(q.supplier.name_ru),
              c(money(q.amount, safe(q.currency, "symbol", ""))),
              c(dt(q.valid_until)),
              c(num(q.last_version or 0)),
              badge_of(q.status, q.get_status_display())]
             for q in qs],
            empty="Предложения не созданы"),
    ]
    return {"blocks": blocks}


def quote_detail_data(request, pk, **kw):
    q = get_object_or_404(
        m.Quote.objects.select_related("supplier", "currency", "rfq"), pk=pk)
    lines = q.lines.select_related("good")
    blocks = [
        fld("Карточка предложения", [
            ("Номер", q.number),
            ("Запрос", safe(q.rfq, "number")),
            ("Поставщик", q.supplier.name_ru),
            ("Базис поставки", q.get_incoterm_display()),
            ("Сумма", money(q.amount, safe(q.currency, "symbol", ""))),
            ("Действует до", dt(q.valid_until)),
            ("Статус", q.get_status_display()),
            ("Комментарий", q.comment or "—"),
        ]),
        tbl("Позиции предложения",
            ["Товар", "Количество", "Цена", "Сумма", "Срок поставки, сут"],
            [[c(safe(line.good, "name_ru")), c(num(line.qty, 3)),
              c(money(line.price)), c(money(line.amount)),
              c(line.delivery_days or "—")]
             for line in lines],
            empty="Позиции не заполнены"),
        tbl("Версии предложения",
            ["Версия", "Изменённые поля", "Автор", "Создана"],
            [[c(num(v.version)), c(v.changed_fields or "—"),
              c(v.author.get_username()), c(dtm(v.created_at))]
             for v in q.versions.select_related("author")],
            empty="Версии не зафиксированы"),
    ]
    return {"blocks": blocks}


# ======================================================================
# M4. Заказы
# ======================================================================

def order_list_data(request, **kw):
    qs = (m.Order.objects
          .select_related("buyer", "supplier", "currency")
          .annotate(n_lines=Count("lines")))
    status = _q(request, "status")
    if status:
        qs = qs.filter(status=status)
    total = m.Order.objects.aggregate(s=Sum("amount"))["s"] or 0
    blocks = [
        kpi("Заказы", [
            k("Всего", m.Order.objects.count()),
            k("В работе", m.Order.objects.filter(
                status__in=["confirmed", "in_production"]).count()),
            k("Отгружено", m.Order.objects.filter(
                status="shipped").count()),
            k("Сумма портфеля", money(total, "CNY")),
        ]),
        tbl("Список заказов",
            ["Номер", "Покупатель", "Поставщик", "Сумма", "Позиций",
             "Подписан", "Статус"],
            [[c(o.number, url_for("order_detail", o.pk), mono=True),
              c(o.buyer.name_ru), c(o.supplier.name_ru),
              c(money(o.amount, safe(o.currency, "symbol", ""))),
              c(num(o.n_lines)), c(dt(o.signed_date)),
              badge_of(o.status, o.get_status_display())]
             for o in qs],
            empty="Заказы не заключены"),
    ]
    return {"blocks": blocks}


def order_detail_data(request, pk, **kw):
    o = get_object_or_404(
        m.Order.objects.select_related(
            "buyer", "supplier", "currency", "quote"), pk=pk)
    blocks = [
        fld("Карточка заказа", [
            ("Номер", o.number),
            ("Покупатель", o.buyer.name_ru),
            ("Поставщик", o.supplier.name_ru),
            ("Основание", safe(o.quote, "number")),
            ("Базис поставки", o.get_incoterm_display()),
            ("Сумма", money(o.amount, safe(o.currency, "symbol", ""))),
            ("Подписан", dt(o.signed_date)),
            ("Статус", o.get_status_display()),
            ("Доля отгрузки", f"{num(o.shipped_share * 100, 1)} %"),
        ]),
        tbl("Позиции заказа",
            ["Товар", "Количество", "Цена", "Сумма", "Срок поставки, сут"],
            [[c(safe(line.good, "name_ru")), c(num(line.qty, 3)),
              c(money(line.price)), c(money(line.amount)),
              c(line.delivery_days or "—")]
             for line in o.lines.select_related("good")],
            empty="Позиции не заполнены"),
        tbl("Этапы исполнения",
            ["Вид этапа", "Плановая дата", "Фактическая дата", "Статус",
             "Ответственный"],
            [[c(mil.get_kind_display()), c(dt(mil.planned_date)),
              c(dt(mil.actual_date)),
              badge_of(mil.status, mil.get_status_display()),
              c(safe(mil.responsible, "get_username", "—"))]
             for mil in o.milestones.select_related("responsible")],
            empty="Этапы не заведены"),
        tbl("Партии",
            ["Номер", "Количество", "Вес, кг", "Дата отгрузки", "Контейнер"],
            [[c(s.number, url_for("shipment_detail", s.pk), mono=True),
              c(num(s.qty, 3)), c(num(s.weight_kg, 1)),
              c(dt(s.ship_date)), c(s.container_no or "—")]
             for s in o.shipments.all()],
            empty="Партии не отгружены"),
        tbl("Документы заказа",
            ["Тип", "Выдан", "Действителен до", "Статус"],
            [[c(safe(d.doc_type, "name_ru")), c(dt(d.issued_date)),
              c(dt(d.valid_until)),
              badge_of(d.status, d.get_status_display())]
             for d in o.documents.select_related("doc_type")],
            empty="Документы не загружены"),
    ]
    return {"blocks": blocks}


def order_milestones_data(request, pk, **kw):
    o = get_object_or_404(m.Order.objects.select_related("buyer",
                                                         "supplier"), pk=pk)
    milestones = o.milestones.select_related("responsible")
    done = milestones.filter(status="done").count()
    blocks = [
        fld("Заказ", [
            ("Номер", o.number),
            ("Покупатель", o.buyer.name_ru),
            ("Поставщик", o.supplier.name_ru),
            ("Статус", o.get_status_display()),
        ]),
        kpi("Ход исполнения", [
            k("Этапов всего", milestones.count()),
            k("Выполнено", done, tone="ok"),
            k("В ожидании", milestones.filter(status="pending").count(),
              tone="warn"),
            k("Просрочено", sum(1 for x in milestones
                                if x.planned_date
                                and x.planned_date < timezone.now().date()
                                and x.status == "pending"), tone="danger"),
        ]),
        tbl("Этапы исполнения заказа",
            ["Вид этапа", "Плановая дата", "Фактическая дата", "Статус",
             "Ответственный"],
            [[c(mil.get_kind_display()), c(dt(mil.planned_date)),
              c(dt(mil.actual_date)),
              badge_of(mil.status, mil.get_status_display()),
              c(safe(mil.responsible, "get_username", "—"))]
             for mil in milestones],
            empty="Этапы не заведены"),
    ]
    return {"blocks": blocks}


def order_changes_data(request, pk, **kw):
    o = get_object_or_404(m.Order.objects, pk=pk)
    blocks = [
        fld("Заказ", [("Номер", o.number),
                      ("Статус", o.get_status_display())]),
        tbl("Листы изменений заказа",
            ["Тип изменения", "Было", "Стало", "Причина", "Инициатор",
             "Согласовал", "Создан"],
            [[c(ch.get_change_type_display()), c(ch.before or "—"),
              c(ch.after or "—"), c(ch.reason or "—"),
              c(safe(ch.initiated_by, "get_username", "—")),
              c(safe(ch.approved_by, "get_username", "—")),
              c(dtm(ch.created_at))]
             for ch in o.changes.select_related(
                 "initiated_by", "approved_by")],
            empty="Изменений не было"),
    ]
    return {"blocks": blocks}


# ======================================================================
# M5. Логистика и пункты пропуска
# ======================================================================

def shipment_list_data(request, **kw):
    qs = (m.Shipment.objects.select_related("order")
          .prefetch_related("transport__lane"))
    blocks = [
        kpi("Партии", [
            k("Всего", m.Shipment.objects.count()),
            k("Перевозок", m.Transport.objects.count(), "оформлено"),
            k("Точек маршрута", m.TrackPoint.objects.count(), "отмечено"),
            k("Инцидентов", m.Incident.objects.exclude(
                status__in=["resolved", "closed"]).count(),
              "открыто", tone="warn"),
        ]),
        tbl("Партии и перевозки",
            ["Номер", "Заказ", "Количество", "Вес, кг", "Дата отгрузки",
             "Контейнер", "Перевозка"],
            [[c(s.number, url_for("shipment_detail", s.pk), mono=True),
              c(s.order.number), c(num(s.qty, 3)), c(num(s.weight_kg, 1)),
              c(dt(s.ship_date)), c(s.container_no or "—"),
              c(_transport_label(s))]
             for s in qs],
            empty="Партии не отгружены"),
    ]
    return {"blocks": blocks}


def _transport_label(shipment):
    tr = safe(shipment, "transport", None)
    if not tr:
        return "не оформлена"
    lane = safe(tr, "lane", None)
    return f"{tr.get_mode_display()}" + (f" · {lane.code}" if lane else "")


def shipment_detail_data(request, pk, **kw):
    s = get_object_or_404(m.Shipment.objects.select_related("order"), pk=pk)
    tr = safe(s, "transport", None)
    blocks = [
        fld("Карточка партии", [
            ("Номер", s.number),
            ("Заказ", s.order.number),
            ("Количество", num(s.qty, 3)),
            ("Вес, кг", num(s.weight_kg, 1)),
            ("Объём, м³", num(s.volume_m3, 2)),
            ("Дата отгрузки", dt(s.ship_date)),
            ("Контейнер", s.container_no or "—"),
            ("Отгружено от заказа", f"{num(s.order.shipped_share * 100, 1)} %"),
        ]),
        tbl("Перевозка",
            ["Перевозчик", "Канал", "Вид транспорта", "Накладная",
             "Стоимость"],
            [[c(_carrier_label(tr)), c(safe(safe(tr, "lane", None), "code",
                                            "—")),
              c(tr.get_mode_display() if tr else "—"),
              c(tr.waybill_no or "—" if tr else "—"),
              c(money(tr.cost) if tr else "—")]] if tr else [],
            empty="Перевозка не оформлена"),
        tbl("Точки маршрута",
            ["Время события", "Место", "Состояние", "Примечание"],
            [[c(dtm(p.event_time)), c(p.place or "—"),
              badge_of(p.status, p.status or "—"), c(p.note or "—")]
             for p in (tr.track_points.all() if tr else [])],
            empty="Точки маршрута не отмечены"),
        tbl("Инциденты партии",
            ["Номер", "Вид", "Критичность", "Описание", "Статус"],
            [[c(i.number, url_for("exception_list"), mono=True),
              c(i.get_kind_display()),
              badge_of(i.severity, i.get_severity_display()),
              c(i.description or "—"),
              badge_of(i.status, i.get_status_display())]
             for i in s.incidents.all()],
            empty="Инцидентов нет"),
        tbl("Документы партии",
            ["Тип", "Выдан", "Действителен до", "Статус"],
            [[c(safe(d.doc_type, "name_ru")), c(dt(d.issued_date)),
              c(dt(d.valid_until)),
              badge_of(d.status, d.get_status_display())]
             for d in s.documents.select_related("doc_type")],
            empty="Документы не загружены"),
    ]
    return {"blocks": blocks}


def _carrier_label(transport):
    if not transport:
        return "—"
    return transport.carrier.name_ru if transport.carrier \
        else (transport.carrier_name or "не указан")


def exception_list_data(request, **kw):
    qs = (m.Incident.objects.select_related("shipment", "reported_by")
          .order_by("-created_at"))
    severity = _q(request, "severity")
    if severity:
        qs = qs.filter(severity=severity)
    blocks = [
        kpi("Инциденты", [
            k("Всего", m.Incident.objects.count()),
            k("Открытых", m.Incident.objects.filter(
                status="registered").count(), tone="warn"),
            k("В обработке", m.Incident.objects.filter(
                status="in_progress").count()),
            k("Критичных", m.Incident.objects.filter(
                severity="critical").count(), tone="danger"),
        ]),
        tbl("Список инцидентов",
            ["Номер", "Партия", "Вид", "Критичность", "Описание",
             "Зарегистрировал", "Статус"],
            [[c(i.number, mono=True), c(safe(i.shipment, "number")),
              c(i.get_kind_display()),
              badge_of(i.severity, i.get_severity_display()),
              c(i.description or "—"),
              c(safe(i.reported_by, "get_username", "—")),
              badge_of(i.status, i.get_status_display())]
             for i in qs],
            empty="Инцидентов нет"),
    ]
    return {"blocks": blocks}


def exception_create_data(request, **kw):
    blocks = [
        tbl("Партии для регистрации инцидента",
            ["Номер", "Заказ", "Дата отгрузки", "Контейнер"],
            [[c(s.number, url_for("shipment_detail", s.pk), mono=True),
              c(s.order.number), c(dt(s.ship_date)),
              c(s.container_no or "—")]
             for s in m.Shipment.objects.select_related("order")],
            empty="Сначала отгрузите партии"),
        tbl("Виды и критичность инцидентов",
            ["Поле", "Допустимые значения"],
            [[c("Вид инцидента"),
              c(" · ".join(v for _, v in m.Incident._meta
                           .get_field("kind").choices))],
             [c("Критичность"),
              c(" · ".join(v for _, v in m.Incident._meta
                           .get_field("severity").choices))],
             [c("Статус"),
              c(" · ".join(v for _, v in m.Incident._meta
                           .get_field("status").choices))]],
            empty="—"),
    ]
    return {"blocks": blocks}


# ======================================================================
# M6. Документы и соответствие
# ======================================================================

def documents_list_data(request, **kw):
    qs = (m.Document.objects
          .select_related("doc_type", "order", "shipment"))
    status = _q(request, "status")
    if status:
        qs = qs.filter(status=status)
    blocks = [
        kpi("Реестр документов", [
            k("Всего", m.Document.objects.count()),
            k("Подписано", m.Document.objects.filter(status="signed").count(),
              tone="ok"),
            k("Истекает ≤ 30 дней", m.Document.objects.filter(
                valid_until__lte=timezone.now().date() +
                timezone.timedelta(days=30)).count(), tone="warn"),
            k("Типов документов", m.DocType.objects.count()),
        ]),
        tbl("Документы",
            ["Тип", "Заказ", "Партия", "Выдал", "Выдан",
             "Действителен до", "Статус"],
            [[c(safe(d.doc_type, "name_ru")), c(safe(d.order, "number")),
              c(safe(d.shipment, "number")), c(d.issuer or "—"),
              c(dt(d.issued_date)), c(dt(d.valid_until)),
              badge_of(d.status, d.get_status_display())]
             for d in qs],
            empty="Документы не загружены"),
    ]
    return {"blocks": blocks}


def documents_upload_data(request, **kw):
    blocks = [
        tbl("Типы документов и этапы",
            ["Код", "Наименование (рус.)", "Наименование (кит.)", "Этап"],
            [[c(t.code, mono=True), c(t.name_ru), c(t.name_zh or "—"),
              badge_of(t.stage, t.get_stage_display())]
             for t in m.DocType.objects.all()],
            empty="Типы документов не заведены"),
        tbl("Заказы для привязки документа",
            ["Номер", "Покупатель", "Статус", "Документов"],
            [[c(o.number, url_for("order_detail", o.pk), mono=True),
              c(o.buyer.name_ru),
              badge_of(o.status, o.get_status_display()),
              c(num(o.documents.count()))]
             for o in m.Order.objects.select_related("buyer")],
            empty="Заказы не заключены"),
    ]
    return {"blocks": blocks}


def certificates_list_data(request, **kw):
    today = timezone.now().date()
    horizon = today + timezone.timedelta(days=30)
    qs = m.Certificate.objects.select_related("good")
    blocks = [
        kpi("Сертификаты", [
            k("Всего", qs.count()),
            k("Истекают ≤ 30 дней", qs.filter(
                valid_until__lte=horizon).count(), tone="warn"),
            k("Истекли", qs.filter(valid_until__lt=today).count(),
              tone="danger"),
            k("Действуют", qs.filter(valid_until__gt=horizon).count(),
              tone="ok"),
        ]),
        tbl("Срок действия сертификатов",
            ["Номер", "Вид", "Товар", "Выдан", "Действителен до",
             "Осталось дней", "ФГИС"],
            [[c(cert.number, mono=True), c(cert.get_kind_display()),
              c(safe(cert.good, "name_ru")), c(dt(cert.issued_date)),
              c(dt(cert.valid_until)),
              badge_of("expired" if cert.days_to_expiry < 0
                       else ("low" if cert.days_to_expiry <= 30 else "ok"),
                       cert.days_to_expiry),
              c(cert.fgis_no or "—")]
             for cert in qs.order_by("valid_until")],
            empty="Сертификаты не заведены"),
    ]
    return {"blocks": blocks}


def compliance_check_data(request, **kw):
    reqs = m.DocRequirement.objects.select_related("order", "doc_type",
                                                   "document")
    checks = m.ComplianceCheck.objects.select_related("order", "checker")
    blocks = [
        kpi("Соответствие", [
            k("Требований", reqs.count(), "в комплектах"),
            k("Не хватает", reqs.filter(status="missing").count(),
              tone="warn"),
            k("Проверок", checks.count(), "выполнено"),
            k("Рисков", m.ComplianceRisk.objects.count(), "выявлено"),
        ]),
        tbl("Комплектность документов по заказам",
            ["Заказ", "Тип документа", "Статус", "Документ", "Примечание"],
            [[c(r.order.number, url_for("order_detail", r.order.pk),
                mono=True),
              c(safe(r.doc_type, "name_ru")),
              badge_of(r.status, r.get_status_display()),
              c(safe(r.document, "id", "не привязан")),
              c(r.note or "—")]
             for r in reqs],
            empty="Требования не заданы"),
        tbl("Выполненные проверки",
            ["Заказ", "Дата проверки", "Результат", "Проверяющий",
             "Примечание"],
            [[c(ch.order.number, url_for("order_detail", ch.order.pk),
                mono=True),
              c(dtm(ch.checked_at)),
              badge_of(ch.result, ch.get_result_display()),
              c(safe(ch.checker, "get_username", "—")),
              c(ch.note or "—")]
             for ch in checks],
            empty="Проверки не выполнялись"),
    ]
    return {"blocks": blocks}


# ======================================================================
# M7. Двуязычное общение
# ======================================================================

def message_list_data(request, **kw):
    qs = (m.Dialog.objects
          .annotate(n_messages=Count("messages"))
          .order_by("-last_message_at"))
    blocks = [
        kpi("Диалоги", [
            k("Всего", m.Dialog.objects.count()),
            k("Открытых", m.Dialog.objects.filter(status="open").count()),
            k("Сообщений", m.Message.objects.count()),
            k("Переводов", m.Translation.objects.count(), "выполнено"),
        ]),
        tbl("Диалоги по бизнес-объектам",
            ["Объект", "Обозначение", "Сообщений", "Последнее сообщение",
             "Статус"],
            [[c(d.get_subject_kind_display()),
              c(d.subject_label or "—"),
              c(num(d.n_messages)), c(dtm(d.last_message_at)),
              badge_of(d.status, d.get_status_display())]
             for d in qs],
            empty="Диалоги не начаты"),
    ]
    return {"blocks": blocks}


def message_detail_data(request, pk, **kw):
    d = get_object_or_404(m.Dialog.objects, pk=pk)
    messages = d.messages.select_related("author").order_by("created_at")
    blocks = [
        fld("Диалог", [
            ("Объект", d.get_subject_kind_display()),
            ("Обозначение", d.subject_label or "—"),
            ("Статус", d.get_status_display()),
            ("Последнее сообщение", dtm(d.last_message_at)),
            ("Участники", ", ".join(
                u.get_username() for u in d.participants.all()) or "—"),
        ]),
        tbl("Сообщения",
            ["Время", "Автор", "Язык", "Текст"],
            [[c(dtm(msg.created_at)), c(msg.author.get_username()),
              c(msg.get_language_display()), c(msg.body)]
             for msg in messages],
            empty="Сообщений нет"),
        tbl("Переводы",
            ["Сообщение", "С языка", "На язык", "Перевод", "Движок"],
            [[c(f"#{tr.message_id}", mono=True),
              c(tr.source_language), c(tr.target_language),
              c(tr.text), c(tr.engine or "—")]
             for tr in m.Translation.objects.filter(
                 message__dialog=d).select_related("message")],
            empty="Переводы не выполнялись"),
    ]
    return {"blocks": blocks}


# ======================================================================
# M8. Задачи и напоминания
# ======================================================================

def task_board_data(request, **kw):
    today = timezone.now().date()
    qs = m.Task.objects.select_related("assignee")
    overdue = [t for t in qs if t.is_overdue]
    blocks = [
        kpi("Доска задач", [
            k("Новых", qs.filter(status="new").count()),
            k("В работе", qs.filter(status="in_progress").count()),
            k("Просрочено", len(overdue), tone="danger"),
            k("Выполнено", qs.filter(status="done").count(), tone="ok"),
        ]),
        tbl("Просроченные задачи",
            ["Номер", "Заголовок", "Исполнитель", "Срок", "Приоритет",
             "Статус"],
            [[c(t.number, url_for("task_detail", t.pk), mono=True),
              c(t.title), c(safe(t.assignee, "get_username", "—")),
              c(dt(t.due_date)),
              badge_of(t.priority, t.get_priority_display()),
              badge_of(t.status, t.get_status_display())]
             for t in overdue],
            empty="Просроченных задач нет"),
        tbl("Все задачи",
            ["Номер", "Заголовок", "Источник", "Исполнитель", "Срок",
             "Приоритет", "Статус"],
            [[c(t.number, url_for("task_detail", t.pk), mono=True),
              c(t.title),
              c(f"{t.get_source_kind_display()} #{t.source_id}"
                if t.source_id else t.get_source_kind_display()),
              c(safe(t.assignee, "get_username", "—")), c(dt(t.due_date)),
              badge_of(t.priority, t.get_priority_display()),
              badge_of(t.status, t.get_status_display())]
             for t in qs.order_by("due_date")],
            empty="Задач нет"),
    ]
    return {"blocks": blocks}


def task_detail_data(request, pk, **kw):
    t = get_object_or_404(m.Task.objects.select_related("assignee"), pk=pk)
    blocks = [
        fld("Карточка задачи", [
            ("Номер", t.number),
            ("Заголовок", t.title),
            ("Источник", f"{t.get_source_kind_display()} #{t.source_id}"
             if t.source_id else t.get_source_kind_display()),
            ("Исполнитель", safe(t.assignee, "get_username", "—")),
            ("Срок", dt(t.due_date)),
            ("Приоритет", t.get_priority_display()),
            ("Статус", t.get_status_display()),
            ("Просрочена", "да" if t.is_overdue else "нет"),
            ("Создана", dt(t.created_at)),
        ]),
        tbl("Напоминания",
            ["Канал", "Время отправки", "Отправлено"],
            [[badge_of(r.channel, r.get_channel_display()),
              c(dtm(r.send_at)), c("да" if r.is_sent else "нет")]
             for r in t.reminders.all()],
            empty="Напоминания не настроены"),
    ]
    return {"blocks": blocks}


def notification_settings_data(request, **kw):
    qs = m.NotificationSetting.objects.select_related("user")
    blocks = [
        tbl("Настройки уведомлений",
            ["Пользователь", "Событие", "Канал", "Включено"],
            [[c(s.user.get_username()),
              badge_of(s.event, s.get_event_display()),
              badge_of(s.channel, s.get_channel_display()),
              c("да" if s.is_enabled else "нет")]
             for s in qs],
            empty="Настройки не заданы"),
        tbl("Последние уведомления",
            ["Получатель", "Вид", "Заголовок", "Прочитано", "Создано"],
            [[c(n.recipient.get_username()), c(n.kind), c(n.title),
              c("да" if n.is_read else "нет"), c(dtm(n.created_at))]
             for n in m.Notification.objects.select_related(
                 "recipient").order_by("-created_at")[:20]],
            empty="Уведомлений нет"),
    ]
    return {"blocks": blocks}


# ======================================================================
# M9. Аналитика
# ======================================================================

def dashboard_data(request, **kw):
    today = timezone.now().date()
    orders = m.Order.objects.all()
    by_status = (orders.values("status")
                 .annotate(n=Count("id"), total=Sum("amount"))
                 .order_by("-n"))
    labels = dict(m.Order._meta.get_field("status").choices)
    blocks = [
        kpi("Панель исполнения", [
            k("Заказы в работе", orders.filter(
                status__in=["confirmed", "in_production"]).count()),
            k("Отгружено", orders.filter(status="shipped").count()),
            k("Инциденты", m.Incident.objects.exclude(
                status__in=["resolved", "closed"]).count(),
              "открыто", tone="warn"),
            k("Документы ≤ 30 дней", m.Document.objects.filter(
                valid_until__lte=today + timezone.timedelta(days=30)
            ).count(), tone="warn"),
            k("Задачи просрочены", sum(1 for t in m.Task.objects.all()
                                       if t.is_overdue), tone="danger"),
            k("Портфель", money(orders.aggregate(
                s=Sum("amount"))["s"] or 0, "CNY")),
        ]),
        tbl("Распределение заказов по статусам",
            ["Статус", "Заказов", "Сумма"],
            [[badge_of(row["status"], labels.get(row["status"], "—")),
              c(num(row["n"])), c(money(row["total"], "CNY"))]
             for row in by_status],
            empty="Заказов нет"),
        tbl("Открытые инциденты",
            ["Номер", "Партия", "Критичность", "Статус", "Зарегистрирован"],
            [[c(i.number, mono=True), c(safe(i.shipment, "number")),
              badge_of(i.severity, i.get_severity_display()),
              badge_of(i.status, i.get_status_display()),
              c(dtm(i.created_at))]
             for i in m.Incident.objects.exclude(
                 status__in=["resolved", "closed"]).select_related(
                     "shipment")],
            empty="Открытых инцидентов нет"),
        tbl("Ближайшие сроки",
            ["Объект", "Событие", "Дата", "Осталось дней"],
            [[c(f"Заказ {o.number}", label="Заказ"),
              c("Плановая дата этапа"),
              c(dt(mil.planned_date)),
              c((mil.planned_date - today).days if mil.planned_date else "—")]
             for o in orders for mil in o.milestones.filter(
                 status="pending", planned_date__isnull=False)
             .order_by("planned_date")[:10]],
            empty="Ближайших сроков нет"),
    ]
    return {"blocks": blocks}


def dashboard_logistics_data(request, **kw):
    lanes = (m.TransportLane.objects
             .annotate(n_transport=Count("transports"),
                       avg_cost=Avg("transports__cost"))
             .select_related("origin", "destination"))
    transports = m.Transport.objects.select_related("lane", "shipment")
    blocks = [
        kpi("Логистика", [
            k("Перевозок", transports.count()),
            k("Каналов", m.TransportLane.objects.count()),
            k("Пунктов пропуска", m.BorderCrossing.objects.count()),
            k("Средняя стоимость",
              money(transports.aggregate(a=Avg("cost"))["a"] or 0)),
        ]),
        tbl("Каналы доставки",
            ["Код", "Маршрут", "Вид", "Срок, сут", "Цена, за кг",
             "Перевозок", "Средняя стоимость"],
            [[c(lane.code, mono=True),
              c(f"{lane.origin.code} → {lane.destination.code}"),
              c(lane.get_mode_display()), c(num(lane.days)),
              c(num(lane.price_per_kg, 3)), c(num(lane.n_transport)),
              c(money(lane.avg_cost))]
             for lane in lanes],
            empty="Каналы не заведены"),
        tbl("Пункты пропуска",
            ["Код", "Наименование", "Режим", "Пропускная способность, т/сут",
             "Среднее пребывание, сут"],
            [[c(b.code, mono=True), c(b.name_ru), c(b.get_mode_display()),
              c(num(b.capacity_t_per_day)),
              c(num(b.dwell_days, 1))]
             for b in m.BorderCrossing.objects.select_related("country")],
            empty="Пункты пропуска не заведены"),
    ]
    return {"blocks": blocks}


def dashboard_compliance_data(request, **kw):
    today = timezone.now().date()
    horizon = today + timezone.timedelta(days=30)
    blocks = [
        kpi("Соответствие", [
            k("Сертификаты ≤ 30 дней", m.Certificate.objects.filter(
                valid_until__lte=horizon).count(), tone="warn"),
            k("Документы ≤ 30 дней", m.Document.objects.filter(
                valid_until__lte=horizon).count(), tone="warn"),
            k("Не хватает документов", m.DocRequirement.objects.filter(
                status="missing").count(), tone="danger"),
            k("Рисков выявлено", m.ComplianceRisk.objects.count()),
        ]),
        tbl("Истекающие сертификаты",
            ["Номер", "Товар", "Действителен до", "Осталось дней"],
            [[c(cert.number, mono=True), c(safe(cert.good, "name_ru")),
              c(dt(cert.valid_until)), c(cert.days_to_expiry)]
             for cert in m.Certificate.objects.filter(
                 valid_until__lte=horizon).select_related("good")
             .order_by("valid_until")],
            empty="Истекающих сертификатов нет"),
        tbl("Недостающие документы",
            ["Заказ", "Тип документа", "Статус", "Примечание"],
            [[c(r.order.number, url_for("order_detail", r.order.pk),
                mono=True),
              c(safe(r.doc_type, "name_ru")),
              badge_of(r.status, r.get_status_display()),
              c(r.note or "—")]
             for r in m.DocRequirement.objects.filter(
                 status="missing").select_related("order", "doc_type")],
            empty="Комплектность в порядке"),
        tbl("Риски соответствия",
            ["Заказ", "Вид риска", "Вероятность", "Влияние", "Уровень",
             "Рекомендация"],
            [[c(r.order.number, url_for("order_detail", r.order.pk),
                mono=True),
              c(r.kind),
              badge_of(r.probability, r.get_probability_display()),
              badge_of(r.impact, r.get_impact_display()),
              badge_of(r.level, r.get_level_display()),
              c(r.advice or "—")]
             for r in m.ComplianceRisk.objects.select_related("order")],
            empty="Рисков не выявлено"),
    ]
    return {"blocks": blocks}


# ======================================================================
# M10. Расчёты и сверка
# ======================================================================

def statement_list_data(request, **kw):
    qs = (m.Statement.objects.select_related("order", "currency")
          .annotate(n_lines=Count("lines")))
    status = _q(request, "status")
    if status:
        qs = qs.filter(status=status)
    paid = m.Payment.objects.aggregate(s=Sum("amount"))["s"] or 0
    blocks = [
        kpi("Расчёты", [
            k("Счетов", m.Statement.objects.count()),
            k("Оплачено", money(paid, "CNY"), tone="ok"),
            k("Сверок", m.Reconciliation.objects.count()),
            k("Разногласий", m.Reconciliation.objects.exclude(
                diff=0).count(), tone="warn"),
        ]),
        tbl("Список счетов",
            ["Номер", "Заказ", "Сумма", "Срок оплаты", "Позиций", "Статус",
             "Подтвердил"],
            [[c(s.number, url_for("statement_detail", s.pk), mono=True),
              c(s.order.number),
              c(money(s.amount, safe(s.currency, "symbol", ""))),
              c(dt(s.due_date)), c(num(s.n_lines)),
              badge_of(s.status, s.get_status_display()),
              c(s.confirmed_by or "—")]
             for s in qs],
            empty="Счета не выставлены"),
    ]
    return {"blocks": blocks}


def statement_detail_data(request, pk, **kw):
    s = get_object_or_404(
        m.Statement.objects.select_related("order", "currency"), pk=pk)
    payments = s.payments.all()
    recon = m.Reconciliation.objects.filter(order=s.order)
    paid = payments.aggregate(s=Sum("amount"))["s"] or 0
    blocks = [
        fld("Карточка счёта", [
            ("Номер", s.number),
            ("Заказ", s.order.number),
            ("Сумма", money(s.amount, safe(s.currency, "symbol", ""))),
            ("Оплачено", money(paid, safe(s.currency, "symbol", ""))),
            ("Срок оплаты", dt(s.due_date)),
            ("Статус", s.get_status_display()),
            ("Подтвердил", s.confirmed_by or "—"),
        ]),
        tbl("Позиции счёта",
            ["Описание", "Количество", "Цена", "Сумма", "Источник"],
            [[c(line.description), c(num(line.qty, 3)),
              c(money(line.price)), c(money(line.amount)),
              badge_of(line.source, line.get_source_display())]
             for line in s.lines.all()],
            empty="Позиции не заполнены"),
        tbl("Сверка расчётов",
            ["Партнёр", "Период", "Наша сумма", "Сумма партнёра",
             "Разница", "Статус"],
            [[c(r.partner), c(r.period),
              c(money(r.our_amount)), c(money(r.partner_amount)),
              badge_of("danger" if r.diff else "ok", money(r.diff)),
              badge_of(r.status, r.get_status_display())]
             for r in recon],
            empty="Сверка не выполнялась"),
        tbl("Подтверждения оплаты",
            ["Дата", "Сумма", "Канал", "Закупщик", "Поставщик"],
            [[c(dt(p.paid_date)), c(money(p.amount)),
              c(p.channel_note or "—"),
              c("да" if p.buyer_confirmed else "нет"),
              c("да" if p.supplier_confirmed else "нет")]
             for p in payments],
            empty="Платежи не зарегистрированы"),
    ]
    return {"blocks": blocks}


# ======================================================================
# M11. Администрирование
# ======================================================================

def audit_log_list_data(request, **kw):
    qs = m.AuditLog.objects.select_related("actor").order_by("-created_at")
    action = _q(request, "action")
    if action:
        qs = qs.filter(action=action)
    blocks = [
        kpi("Журнал аудита", [
            k("Записей", m.AuditLog.objects.count()),
            k("Пользователей", m.AuditLog.objects.values(
                "actor").distinct().count(), "в журнале"),
            k("Видов объектов", m.AuditLog.objects.values(
                "target_kind").distinct().count()),
            k("Последняя запись", dtm(m.AuditLog.objects.order_by(
                "-created_at").values_list("created_at", flat=True).first())),
        ]),
        tbl("Записи журнала (только чтение)",
            ["Время", "Пользователь", "Действие", "Объект", "Было", "Стало",
             "IP-адрес"],
            [[c(dtm(log.created_at)),
              c(safe(log.actor, "get_username", "система")),
              badge_of(log.action, log.action),
              c(f"{log.target_kind} #{log.target_id}"),
              c(log.before or "—"), c(log.after or "—"),
              c(log.ip_address or "—")]
             for log in qs],
            empty="Журнал пуст"),
    ]
    return {"blocks": blocks}


def dictionary_list_data(request, **kw):
    blocks = [
        kpi("Справочники", [
            k("Страны", m.Country.objects.count()),
            k("Валюты", m.Currency.objects.count()),
            k("Единицы измерения", m.Uom.objects.count()),
            k("Категории товаров", m.GoodCategory.objects.count()),
            k("Пункты пропуска", m.BorderCrossing.objects.count()),
            k("Типы документов", m.DocType.objects.count()),
        ]),
        tbl("Страны", ["Код", "Наименование", "Валюта", "Часовой пояс"],
            [[c(x.code2, mono=True), c(x.name_ru),
              c(safe(x.currency, "code")), c(x.timezone or "—")]
             for x in m.Country.objects.select_related("currency")],
            empty="Справочник пуст"),
        tbl("Валюты", ["Код", "Наименование", "Символ", "Знаков"],
            [[c(x.code, mono=True), c(x.name_ru), c(x.symbol),
              c(num(x.decimals))] for x in m.Currency.objects.all()],
            empty="Справочник пуст"),
        tbl("Единицы измерения", ["Код", "Наименование", "Вид"],
            [[c(x.code, mono=True), c(x.name_ru), c(x.get_kind_display())]
             for x in m.Uom.objects.all()],
            empty="Справочник пуст"),
        tbl("Типы документов", ["Код", "Наименование", "Этап"],
            [[c(x.code, mono=True), c(x.name_ru),
              badge_of(x.stage, x.get_stage_display())]
             for x in m.DocType.objects.all()],
            empty="Справочник пуст"),
        tbl("Отрасли", ["Код", "Наименование"],
            [[c(x.code, mono=True), c(x.name_ru)]
             for x in m.Industry.objects.all()],
            empty="Справочник пуст"),
    ]
    return {"blocks": blocks}


# ======================================================================
# Реестр провайдеров
# ======================================================================

PAGE_DATA = {
    # M0
    "index": index_data,
    # M1
    "enterprise_profile": enterprise_profile_data,
    "enterprise_verification": enterprise_verification_data,
    "enterprise_members": enterprise_members_data,
    "enterprise_invitations": enterprise_invitations_data,
    # M2
    "goods_list": goods_list_data,
    "goods_detail": goods_detail_data,
    "goods_form": goods_form_data,
    # M3
    "rfq_list": rfq_list_data,
    "rfq_create": rfq_create_data,
    "rfq_detail": rfq_detail_data,
    "quote_list": quote_list_data,
    "quote_detail": quote_detail_data,
    # M4
    "order_list": order_list_data,
    "order_detail": order_detail_data,
    "order_milestones": order_milestones_data,
    "order_changes": order_changes_data,
    # M5
    "shipment_list": shipment_list_data,
    "shipment_detail": shipment_detail_data,
    "exception_list": exception_list_data,
    "exception_create": exception_create_data,
    # M6
    "documents_list": documents_list_data,
    "documents_upload": documents_upload_data,
    "certificates_list": certificates_list_data,
    "compliance_check": compliance_check_data,
    # M7
    "message_list": message_list_data,
    "message_detail": message_detail_data,
    # M8
    "task_board": task_board_data,
    "task_detail": task_detail_data,
    "notification_settings": notification_settings_data,
    # M9
    "dashboard": dashboard_data,
    "dashboard_logistics": dashboard_logistics_data,
    "dashboard_compliance": dashboard_compliance_data,
    # M10
    "statement_list": statement_list_data,
    "statement_detail": statement_detail_data,
    # M11
    "audit_log_list": audit_log_list_data,
    "dictionary_list": dictionary_list_data,
}


def provider_for(name):
    """Провайдер данных страницы или None (страница остаётся прототипом)."""
    return PAGE_DATA.get(name)


def coverage():
    """(страницы с данными, страницы-прототипы) — для tools/check_data.py."""
    from .pages import PAGES
    wired = [p["name"] for p in PAGES if p["name"] in PAGE_DATA]
    proto = [p["name"] for p in PAGES if p["name"] not in PAGE_DATA]
    return wired, proto
