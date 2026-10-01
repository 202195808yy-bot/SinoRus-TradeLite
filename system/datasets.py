# -*- coding: utf-8 -*-
"""系统管理 的页面数据提供器。

区块构造器与工具函数在 ``core/datasets.py``；
这里只放本应用页面自己的取数逻辑，并在模块末尾
用 ``PROVIDERS`` 声明页面名到提供器的映射。
"""

from decimal import Decimal


from core.datasets import (badge_of, c, dtm, k, kpi, num, q_param, safe, tbl)
from catalog.models import Country, Currency, GoodCategory, Industry, Uom
from documents.models import DocType
from logistics.models import BorderCrossing
from system.models import AuditLog


def audit_log_list_data(request, **kw):
    qs = AuditLog.objects.select_related("actor").order_by("-created_at")
    action = q_param(request, "action")
    if action:
        qs = qs.filter(action=action)
    blocks = [
        kpi("Журнал аудита", [
            k("Записей", AuditLog.objects.count()),
            k("Пользователей", AuditLog.objects.values(
                "actor").distinct().count(), "в журнале"),
            k("Видов объектов", AuditLog.objects.values(
                "target_kind").distinct().count()),
            k("Последняя запись", dtm(AuditLog.objects.order_by(
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
            k("Страны", Country.objects.count()),
            k("Валюты", Currency.objects.count()),
            k("Единицы измерения", Uom.objects.count()),
            k("Категории товаров", GoodCategory.objects.count()),
            k("Пункты пропуска", BorderCrossing.objects.count()),
            k("Типы документов", DocType.objects.count()),
        ]),
        tbl("Страны", ["Код", "Наименование", "Валюта", "Часовой пояс"],
            [[c(x.code2, mono=True), c(x.name_ru),
              c(safe(x.currency, "code")), c(x.timezone or "—")]
             for x in Country.objects.select_related("currency")],
            empty="Справочник пуст"),
        tbl("Валюты", ["Код", "Наименование", "Символ", "Знаков"],
            [[c(x.code, mono=True), c(x.name_ru), c(x.symbol),
              c(num(x.decimals))] for x in Currency.objects.all()],
            empty="Справочник пуст"),
        tbl("Единицы измерения", ["Код", "Наименование", "Вид"],
            [[c(x.code, mono=True), c(x.name_ru), c(x.get_kind_display())]
             for x in Uom.objects.all()],
            empty="Справочник пуст"),
        tbl("Типы документов", ["Код", "Наименование", "Этап"],
            [[c(x.code, mono=True), c(x.name_ru),
              badge_of(x.stage, x.get_stage_display())]
             for x in DocType.objects.all()],
            empty="Справочник пуст"),
        tbl("Отрасли", ["Код", "Наименование"],
            [[c(x.code, mono=True), c(x.name_ru)]
             for x in Industry.objects.all()],
            empty="Справочник пуст"),
    ]
    return {"blocks": blocks}


#: 本应用页面的提供器（在 ``apps.ready()`` 中登记）。
PROVIDERS = {
    "audit_log_list": audit_log_list_data,
    "dictionary_list": dictionary_list_data,
}
