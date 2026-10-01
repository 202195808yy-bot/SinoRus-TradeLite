# -*- coding: utf-8 -*-
"""数据看板 的页面数据提供器。

区块构造器与工具函数在 ``core/datasets.py``；
这里只放本应用页面自己的取数逻辑，并在模块末尾
用 ``PROVIDERS`` 声明页面名到提供器的映射。
"""

from decimal import Decimal

from django.utils import timezone
from django.db.models import Avg, Count, Sum

from core.datasets import (badge_of, c, dt, dtm, k, kpi, money, num, safe, tbl, url_for)
from analytics.models import ComplianceRisk
from documents.models import Certificate, DocRequirement, Document
from logistics.models import BorderCrossing, Incident, Transport, TransportLane
from tasks.models import Task
from trading.models import Order


def dashboard_data(request, **kw):
    today = timezone.now().date()
    orders = Order.objects.all()
    by_status = (orders.values("status")
                 .annotate(n=Count("id"), total=Sum("amount"))
                 .order_by("-n"))
    labels = dict(Order._meta.get_field("status").choices)
    blocks = [
        kpi("Панель исполнения", [
            k("Заказы в работе", orders.filter(
                status__in=["confirmed", "in_production"]).count()),
            k("Отгружено", orders.filter(status="shipped").count()),
            k("Инциденты", Incident.objects.exclude(
                status__in=["resolved", "closed"]).count(),
              "открыто", tone="warn"),
            k("Документы ≤ 30 дней", Document.objects.filter(
                valid_until__lte=today + timezone.timedelta(days=30)
            ).count(), tone="warn"),
            k("Задачи просрочены", sum(1 for t in Task.objects.all()
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
             for i in Incident.objects.exclude(
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
    lanes = (TransportLane.objects
             .annotate(n_transport=Count("transports"),
                       avg_cost=Avg("transports__cost"))
             .select_related("origin", "destination"))
    transports = Transport.objects.select_related("lane", "shipment")
    blocks = [
        kpi("Логистика", [
            k("Перевозок", transports.count()),
            k("Каналов", TransportLane.objects.count()),
            k("Пунктов пропуска", BorderCrossing.objects.count()),
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
             for b in BorderCrossing.objects.select_related("country")],
            empty="Пункты пропуска не заведены"),
    ]
    return {"blocks": blocks}


def dashboard_compliance_data(request, **kw):
    today = timezone.now().date()
    horizon = today + timezone.timedelta(days=30)
    blocks = [
        kpi("Соответствие", [
            k("Сертификаты ≤ 30 дней", Certificate.objects.filter(
                valid_until__lte=horizon).count(), tone="warn"),
            k("Документы ≤ 30 дней", Document.objects.filter(
                valid_until__lte=horizon).count(), tone="warn"),
            k("Не хватает документов", DocRequirement.objects.filter(
                status="missing").count(), tone="danger"),
            k("Рисков выявлено", ComplianceRisk.objects.count()),
        ]),
        tbl("Истекающие сертификаты",
            ["Номер", "Товар", "Действителен до", "Осталось дней"],
            [[c(cert.number, mono=True), c(safe(cert.good, "name_ru")),
              c(dt(cert.valid_until)), c(cert.days_to_expiry)]
             for cert in Certificate.objects.filter(
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
             for r in DocRequirement.objects.filter(
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
             for r in ComplianceRisk.objects.select_related("order")],
            empty="Рисков не выявлено"),
    ]
    return {"blocks": blocks}


#: 本应用页面的提供器（在 ``apps.ready()`` 中登记）。
PROVIDERS = {
    "dashboard": dashboard_data,
    "dashboard_compliance": dashboard_compliance_data,
    "dashboard_logistics": dashboard_logistics_data,
}
