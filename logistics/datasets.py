# -*- coding: utf-8 -*-
"""物流与口岸 的页面数据提供器。

区块构造器与工具函数在 ``core/datasets.py``；
这里只放本应用页面自己的取数逻辑，并在模块末尾
用 ``PROVIDERS`` 声明页面名到提供器的映射。
"""

from decimal import Decimal

from django.shortcuts import get_object_or_404

from core.datasets import (badge_of, c, dt, dtm, fld, k, kpi, money, num, q_param, safe, tbl, url_for)
from logistics.models import Incident, Shipment, TrackPoint, Transport


def shipment_list_data(request, **kw):
    qs = (Shipment.objects.select_related("order")
          .prefetch_related("transport__lane"))
    blocks = [
        kpi("Партии", [
            k("Всего", Shipment.objects.count()),
            k("Перевозок", Transport.objects.count(), "оформлено"),
            k("Точек маршрута", TrackPoint.objects.count(), "отмечено"),
            k("Инцидентов", Incident.objects.exclude(
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
    s = get_object_or_404(Shipment.objects.select_related("order"), pk=pk)
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
    qs = (Incident.objects.select_related("shipment", "reported_by")
          .order_by("-created_at"))
    severity = q_param(request, "severity")
    if severity:
        qs = qs.filter(severity=severity)
    blocks = [
        kpi("Инциденты", [
            k("Всего", Incident.objects.count()),
            k("Открытых", Incident.objects.filter(
                status="registered").count(), tone="warn"),
            k("В обработке", Incident.objects.filter(
                status="in_progress").count()),
            k("Критичных", Incident.objects.filter(
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
             for s in Shipment.objects.select_related("order")],
            empty="Сначала отгрузите партии"),
        tbl("Виды и критичность инцидентов",
            ["Поле", "Допустимые значения"],
            [[c("Вид инцидента"),
              c(" · ".join(v for _, v in Incident._meta
                           .get_field("kind").choices))],
             [c("Критичность"),
              c(" · ".join(v for _, v in Incident._meta
                           .get_field("severity").choices))],
             [c("Статус"),
              c(" · ".join(v for _, v in Incident._meta
                           .get_field("status").choices))]],
            empty="—"),
    ]
    return {"blocks": blocks}


#: 本应用页面的提供器（在 ``apps.ready()`` 中登记）。
PROVIDERS = {
    "exception_create": exception_create_data,
    "exception_list": exception_list_data,
    "shipment_detail": shipment_detail_data,
    "shipment_list": shipment_list_data,
}
