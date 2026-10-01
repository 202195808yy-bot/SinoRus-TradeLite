# -*- coding: utf-8 -*-
"""单证与合规 的页面数据提供器。

区块构造器与工具函数在 ``core/datasets.py``；
这里只放本应用页面自己的取数逻辑，并在模块末尾
用 ``PROVIDERS`` 声明页面名到提供器的映射。
"""

from decimal import Decimal

from django.utils import timezone

from core.datasets import (badge_of, c, dt, dtm, k, kpi, num, q_param, safe, tbl, url_for)
from analytics.models import ComplianceRisk
from documents.models import Certificate, ComplianceCheck, DocRequirement, DocType, Document
from trading.models import Order


def documents_list_data(request, **kw):
    qs = (Document.objects
          .select_related("doc_type", "order", "shipment"))
    status = q_param(request, "status")
    if status:
        qs = qs.filter(status=status)
    blocks = [
        kpi("Реестр документов", [
            k("Всего", Document.objects.count()),
            k("Подписано", Document.objects.filter(status="signed").count(),
              tone="ok"),
            k("Истекает ≤ 30 дней", Document.objects.filter(
                valid_until__lte=timezone.now().date() +
                timezone.timedelta(days=30)).count(), tone="warn"),
            k("Типов документов", DocType.objects.count()),
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
             for t in DocType.objects.all()],
            empty="Типы документов не заведены"),
        tbl("Заказы для привязки документа",
            ["Номер", "Покупатель", "Статус", "Документов"],
            [[c(o.number, url_for("order_detail", o.pk), mono=True),
              c(o.buyer.name_ru),
              badge_of(o.status, o.get_status_display()),
              c(num(o.documents.count()))]
             for o in Order.objects.select_related("buyer")],
            empty="Заказы не заключены"),
    ]
    return {"blocks": blocks}


def certificates_list_data(request, **kw):
    today = timezone.now().date()
    horizon = today + timezone.timedelta(days=30)
    qs = Certificate.objects.select_related("good")
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
    reqs = DocRequirement.objects.select_related("order", "doc_type",
                                                   "document")
    checks = ComplianceCheck.objects.select_related("order", "checker")
    blocks = [
        kpi("Соответствие", [
            k("Требований", reqs.count(), "в комплектах"),
            k("Не хватает", reqs.filter(status="missing").count(),
              tone="warn"),
            k("Проверок", checks.count(), "выполнено"),
            k("Рисков", ComplianceRisk.objects.count(), "выявлено"),
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


#: 本应用页面的提供器（在 ``apps.ready()`` 中登记）。
PROVIDERS = {
    "certificates_list": certificates_list_data,
    "compliance_check": compliance_check_data,
    "documents_list": documents_list_data,
    "documents_upload": documents_upload_data,
}
