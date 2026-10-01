# -*- coding: utf-8 -*-
"""结算与对账 的页面数据提供器。

区块构造器与工具函数在 ``core/datasets.py``；
这里只放本应用页面自己的取数逻辑，并在模块末尾
用 ``PROVIDERS`` 声明页面名到提供器的映射。
"""

from decimal import Decimal

from django.shortcuts import get_object_or_404
from django.db.models import Count, Sum

from core.datasets import (badge_of, c, dt, fld, k, kpi, money, num, q_param, safe, tbl, url_for)
from billing.models import Payment, Reconciliation, Statement


def statement_list_data(request, **kw):
    qs = (Statement.objects.select_related("order", "currency")
          .annotate(n_lines=Count("lines")))
    status = q_param(request, "status")
    if status:
        qs = qs.filter(status=status)
    paid = Payment.objects.aggregate(s=Sum("amount"))["s"] or 0
    blocks = [
        kpi("Расчёты", [
            k("Счетов", Statement.objects.count()),
            k("Оплачено", money(paid, "CNY"), tone="ok"),
            k("Сверок", Reconciliation.objects.count()),
            k("Разногласий", Reconciliation.objects.exclude(
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
        Statement.objects.select_related("order", "currency"), pk=pk)
    payments = s.payments.all()
    recon = Reconciliation.objects.filter(order=s.order)
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


#: 本应用页面的提供器（在 ``apps.ready()`` 中登记）。
PROVIDERS = {
    "statement_detail": statement_detail_data,
    "statement_list": statement_list_data,
}
