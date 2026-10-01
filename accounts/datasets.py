# -*- coding: utf-8 -*-
"""企业与账号 的页面数据提供器。

区块构造器与工具函数在 ``core/datasets.py``；
这里只放本应用页面自己的取数逻辑，并在模块末尾
用 ``PROVIDERS`` 声明页面名到提供器的映射。
"""

from decimal import Decimal

from django.utils import timezone
from django.db.models import Q

from core.datasets import (badge_of, c, current_enterprise, demo_mode, dt, fld, k, kpi, safe, tbl)
from accounts.models import Counterparty, Invitation, Membership
from documents.models import Certificate, Document
from trading.models import Order


def enterprise_profile_data(request, **kw):
    ent, demo = current_enterprise(request)
    if ent is None:
        return {"blocks": [], "mode": "demo"}
    member = Membership.objects.filter(
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
            k("Членство", Membership.objects.filter(
                enterprise=ent, is_active=True).count(), "сотрудников"),
            k("Контрагенты", Counterparty.objects.filter(
                enterprise=ent).count(), "в справочнике"),
            k("Заказы", Order.objects.filter(
                Q(buyer=ent) | Q(supplier=ent)).count(), "всего"),
            k("Приглашения", Invitation.objects.filter(
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
                       for cp in Counterparty.objects.filter(
                           enterprise=ent)[:20]],
                      empty="Контрагенты не заведены"))
    return {"blocks": blocks, "mode": demo_mode(demo)}


def enterprise_verification_data(request, **kw):
    ent, demo = current_enterprise(request)
    if ent is None:
        return {"blocks": [], "mode": "demo"}
    docs = (Document.objects
            .filter(Q(order__buyer=ent) | Q(order__supplier=ent))
            .select_related("doc_type", "order"))
    certs = Certificate.objects.all()
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
    return {"blocks": blocks, "mode": demo_mode(demo)}


def enterprise_members_data(request, **kw):
    ent, demo = current_enterprise(request)
    qs = Membership.objects.select_related("user", "enterprise")
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
    return {"blocks": blocks, "mode": demo_mode(demo)}


def enterprise_invitations_data(request, **kw):
    ent, demo = current_enterprise(request)
    qs = Invitation.objects.select_related("enterprise", "invited_by")
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
    return {"blocks": blocks, "mode": demo_mode(demo)}


#: 本应用页面的提供器（在 ``apps.ready()`` 中登记）。
PROVIDERS = {
    "enterprise_invitations": enterprise_invitations_data,
    "enterprise_members": enterprise_members_data,
    "enterprise_profile": enterprise_profile_data,
    "enterprise_verification": enterprise_verification_data,
}
