# -*- coding: utf-8 -*-
"""询价、报价与订单 的页面数据提供器。

区块构造器与工具函数在 ``core/datasets.py``；
这里只放本应用页面自己的取数逻辑，并在模块末尾
用 ``PROVIDERS`` 声明页面名到提供器的映射。
"""

from decimal import Decimal

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count, Max, Sum

from core.datasets import (badge_of, c, dt, dtm, fld, k, kpi, money, num, q_param, safe, tbl, url_for)
from catalog.models import Currency, Good
from trading.models import Order, Quote, QuoteVersion, Rfq, RfqLine


def rfq_list_data(request, **kw):
    qs = (Rfq.objects
          .select_related("buyer", "currency")
          .annotate(n_lines=Count("lines")))
    status = q_param(request, "status")
    if status:
        qs = qs.filter(status=status)
    blocks = [
        kpi("Запросы", [
            k("Всего", Rfq.objects.count()),
            k("Ожидают ответа", Rfq.objects.filter(
                status="sent").count(), tone="warn"),
            k("С предложениями", Rfq.objects.filter(
                status="quoted").count()),
            k("Позиций", RfqLine.objects.count(), "всего"),
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
             for g in Good.objects.filter(
                 is_active=True).select_related("uom")],
            empty="Сначала заведите товары"),
        tbl("Валюты расчётов",
            ["Код", "Наименование", "Символ", "Знаков"],
            [[c(cur.code, mono=True), c(cur.name_ru), c(cur.symbol),
              c(num(cur.decimals))]
             for cur in Currency.objects.all()],
            empty="Валюты не заведены"),
    ]
    return {"blocks": blocks}


def rfq_detail_data(request, pk, **kw):
    r = get_object_or_404(
        Rfq.objects.select_related("buyer", "currency"), pk=pk)
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
    qs = (Quote.objects
          .select_related("supplier", "currency", "rfq")
          .annotate(n_lines=Count("lines", distinct=True),
                    last_version=Max("versions__version")))
    status = q_param(request, "status")
    if status:
        qs = qs.filter(status=status)
    blocks = [
        kpi("Предложения", [
            k("Всего", Quote.objects.count()),
            k("Действующих", Quote.objects.filter(
                status="sent").count(), "ожидают решения"),
            k("Принятых", Quote.objects.filter(status="accepted").count(),
              tone="ok"),
            k("Версий", QuoteVersion.objects.count(), "изменений"),
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
        Quote.objects.select_related("supplier", "currency", "rfq"), pk=pk)
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


def order_list_data(request, **kw):
    qs = (Order.objects
          .select_related("buyer", "supplier", "currency")
          .annotate(n_lines=Count("lines")))
    status = q_param(request, "status")
    if status:
        qs = qs.filter(status=status)
    total = Order.objects.aggregate(s=Sum("amount"))["s"] or 0
    blocks = [
        kpi("Заказы", [
            k("Всего", Order.objects.count()),
            k("В работе", Order.objects.filter(
                status__in=["confirmed", "in_production"]).count()),
            k("Отгружено", Order.objects.filter(
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
        Order.objects.select_related(
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
    o = get_object_or_404(Order.objects.select_related("buyer",
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
    o = get_object_or_404(Order.objects, pk=pk)
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


#: 本应用页面的提供器（在 ``apps.ready()`` 中登记）。
PROVIDERS = {
    "order_changes": order_changes_data,
    "order_detail": order_detail_data,
    "order_list": order_list_data,
    "order_milestones": order_milestones_data,
    "quote_detail": quote_detail_data,
    "quote_list": quote_list_data,
    "rfq_create": rfq_create_data,
    "rfq_detail": rfq_detail_data,
    "rfq_list": rfq_list_data,
}
