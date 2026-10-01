# -*- coding: utf-8 -*-
"""用“一站式”交易的演示数据填充数据库。

用法::

    python manage.py seed_demo

命令是幂等的：重复运行不会重复创建记录
（按唯一特征使用 ``get_or_create``）。

场景：一家俄罗斯采购公司
向中国供应商采购一批医疗设备——询价单、
带版本管理的报价、订单、经后贝加尔斯克的
铁路通道发货、海关异常事件、双语
往来函电、任务、账单与付款登记。
"""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from portal import models as m

DEMO_PASSWORD = "Waxx2003"
TODAY = timezone.localdate()


def days(n):
    return TODAY + timedelta(days=n)


class Command(BaseCommand):
    help = "Создать демонстрационные данные предметной области"

    @transaction.atomic
    def handle(self, *args, **options):
        created = {"n": 0}
        verbose = int(options.get("verbosity", 1)) > 0

        def log(text):
            if verbose:
                self.stdout.write(text)

        def heading(text):
            if verbose:
                self.stdout.write(self.style.MIGRATE_HEADING(text))

        def get(Model, label, defaults=None, **key):
            obj, was = Model.objects.get_or_create(
                defaults=defaults or {}, **key)
            created["n"] += int(was)
            log(f"  {'+' if was else '='} {label}: {obj}")
            return obj

        heading("Справочники (С)")
        cny = get(m.Currency, "валюта", dict(name_ru="Юань", name_zh="人民币",
                                             symbol="¥", decimals=2),
                  code="CNY")
        rub = get(m.Currency, "валюта", dict(name_ru="Рубль", name_zh="卢布",
                                             symbol="₽", decimals=2),
                  code="RUB")
        cn = get(m.Country, "страна", dict(name_ru="Китай", name_zh="中国",
                                           currency=cny,
                                           timezone="Asia/Shanghai"),
                 code2="CN")
        ru = get(m.Country, "страна", dict(name_ru="Россия", name_zh="俄罗斯",
                                           currency=rub,
                                           timezone="Europe/Moscow"),
                 code2="RU")
        pcs = get(m.Uom, "ед. изм.", dict(name_ru="штука", name_zh="件",
                                          kind="count"), code="pcs")
        kg = get(m.Uom, "ед. изм.", dict(name_ru="килограмм", name_zh="千克",
                                         kind="weight"), code="kg")
        med = get(m.Industry, "отрасль",
                  dict(name_ru="Медицинская техника",
                       name_zh="医疗器械"),
                  code="medtech")
        cats = {}
        for code, r_, z_, lvl in [
            ("MED", "Медицинское оборудование", "医疗设备", 1),
            ("MED-PH", "Физиотерапия", "理疗设备", 2),
        ]:
            cats[code] = get(m.GoodCategory, "категория",
                             dict(name_ru=r_, name_zh=z_, level=lvl,
                                  parent=None), code=code)
        bcx_zab = get(m.BorderCrossing, "пункт пропуска",
                      dict(name_ru="Забайкальск", name_zh="后贝加尔斯克",
                           mode="rail", country=ru,
                           capacity_t_per_day=Decimal("600"),
                           dwell_days=Decimal("2.5")), code="ZAB")
        bcx_mzh = get(m.BorderCrossing, "пункт пропуска",
                      dict(name_ru="Маньчжурия", name_zh="满洲里",
                           mode="rail", country=cn,
                           capacity_t_per_day=Decimal("800"),
                           dwell_days=Decimal("1.5")), code="MZM")
        lane = get(m.TransportLane, "канал",
                   dict(name="Забайкальск — Маньчжурия (широкая колея)",
                        origin=bcx_zab, destination=bcx_mzh, mode="rail",
                        days=Decimal("3.0"),
                        price_per_kg=Decimal("0.85")), code="RAIL-ZAB-MZH")
        get(m.Tariff, "тариф", dict(duty_rate=Decimal("0.00"),
                                    vat_rate=Decimal("20.00"),
                                    valid_from=days(-400)),
            hs_code="9019101900")

        heading("Участники (O)")
        ru_co = get(m.Enterprise, "предприятие",
                    dict(name_zh="俄罗斯医疗采购公司", country=ru,
                         industry=med, tin="7710123456",
                         address="Москва, Пресненская наб., 10",
                         bank_account="40702810200000012345",
                         status="active"),
                    name_ru="Медтех-Рус")
        cn_co = get(m.Enterprise, "предприятие",
                    dict(name_zh="杭州康泰医疗科技有限公司", country=cn,
                         industry=med, tin="91330100MA2H2XYZ77",
                         address="Hangzhou, Binjiang District, Jiahe Rd. 88",
                         status="active"),
                    name_ru="Ханчжоу Кантай Медикал")
        log_co = get(m.Enterprise, "предприятие",
                     dict(name_zh="铁路货运代理（哈尔滨）", country=ru,
                          tin="7707111222", status="active"),
                     name_ru="ТрансЛогистик-РЖД")

        users = {}
        for uname, first, last, lang, phone in [
            ("ivanov", "Иван", "Иванов", "ru", "+79001234567"),
            ("wang", "Ван", "Вэй", "zh", "+8613800001111"),
            ("petrov", "Пётр", "Петров", "ru", "+79007654321"),
        ]:
            u, was = User.objects.get_or_create(
                username=uname,
                defaults=dict(email=f"{uname}@tradehub.local",
                              first_name=first, last_name=last))
            created["n"] += int(was)
            if was:
                u.set_password(DEMO_PASSWORD)
                u.save()
            users[uname] = u
            m.Profile.objects.get_or_create(
                user=u, defaults=dict(language=lang, phone=phone))
        admin_u, admin_was = User.objects.get_or_create(
            username="admin",
            defaults=dict(email="admin@tradehub.local",
                          is_staff=True, is_superuser=True))
        created["n"] += int(admin_was)
        # 管理员密码在创建时设置，并且当记录残留
        # 空密码时会被恢复：这是旧版命令
        # 创建它导致的问题，当时无法登录 /admin/。
        if admin_was or not admin_u.password:
            admin_u.set_password(DEMO_PASSWORD)
            admin_u.is_staff = True
            admin_u.is_superuser = True
            admin_u.save()
        log(f"  = пользователи: {len(users)} + admin"
                          f" (пароль: {DEMO_PASSWORD})")

        m.Membership.objects.get_or_create(
            user=users["ivanov"], enterprise=ru_co,
            defaults=dict(role="buyer", department="Снабжение"))
        m.Membership.objects.get_or_create(
            user=users["wang"], enterprise=cn_co,
            defaults=dict(role="supplier"))
        m.Membership.objects.get_or_create(
            user=users["petrov"], enterprise=log_co,
            defaults=dict(role="logistics"))
        m.Invitation.objects.get_or_create(
            code="INV-DEMO-0001",
            defaults=dict(email="accountant@medtech-ru.local",
                          enterprise=ru_co, role="finance",
                          valid_until=days(14),
                          invited_by=users["ivanov"]))
        m.Counterparty.objects.get_or_create(
            enterprise=ru_co, name=cn_co.name_ru,
            defaults=dict(contact_person="Ван Вэй", phone="+8613800001111",
                          default_currency=cny, incoterm="DAP"))

        heading("Товары (T)")
        good = get(m.Good, "товар",
                   dict(hs_code="9019101900",
                        name_ru="Инфракрасный терапевтический аппарат"
                                " ИКТ-150",
                        name_zh="红外线治疗仪", category=cats["MED-PH"],
                        uom=pcs, brand="KangTai", shelf_life_days=1825,
                        attributes={"Мощность": "150 Вт",
                                    "Напряжение": "220 В",
                                    "Гарантия": "24 мес."}),
                   sku="KT-IKT-150")
        m.Packaging.objects.get_or_create(
            good=good, kind="box",
            defaults=dict(units_per_pack=1, unit_weight_kg=Decimal("18.5"),
                          dims="60x45x35"))

        heading(
            "Сделка: запрос → предложение → заказ")
        rfq = m.Rfq.objects.filter(title__startswith="Партия ИКТ").first()
        if rfq is None:
            rfq = m.Rfq.objects.create(
                buyer=ru_co,
                title="Партия ИКТ-150 для клиник ЦФО (60 шт.)",
                due_date=days(-25), incoterm="DAP", currency=cny,
                status="quoted",
                comment="Требуется регистрация в Росздравнадзоре")
            created["n"] += 1
            m.RfqLine.objects.create(rfq=rfq, good=good,
                                     qty=Decimal("60.000"),
                                     target_price=Decimal("180.00"),
                                     requirement="Упаковка по одному")
        quote = m.Quote.objects.filter(rfq=rfq, supplier=cn_co).first()
        if quote is None:
            quote = m.Quote.objects.create(
                rfq=rfq, supplier=cn_co, valid_until=days(5),
                incoterm="DAP", currency=cny,
                amount=Decimal("10800.00"), status="accepted",
                comment="Отгрузка двумя партиями")
            created["n"] += 1
            m.QuoteLine.objects.create(
                quote=quote, good=good, qty=Decimal("60.000"),
                price=Decimal("180.00"), delivery_days=30)
            m.QuoteVersion.objects.create(quote=quote, version=1,
                                          changed_fields="",
                                          author=users["wang"])
            m.QuoteVersion.objects.create(
                quote=quote, version=2,
                changed_fields="valid_until, amount",
                comment="Скорректирован срок действия",
                author=users["wang"])

        order = m.Order.objects.filter(quote=quote).first()
        if order is None:
            order = m.Order.objects.create(
                buyer=ru_co, supplier=cn_co, quote=quote, incoterm="DAP",
                currency=cny, amount=Decimal("10800.00"),
                status="in_production", signed_date=days(-20))
            created["n"] += 1
            m.OrderLine.objects.create(order=order, good=good,
                                       qty=Decimal("60.000"),
                                       price=Decimal("180.00"),
                                       delivery_days=30)
            for kind, off, done in [
                ("contract", -20, True), ("prepayment", -18, True),
                ("production", -5, False), ("packing", 8, False),
                ("shipment", 15, False), ("customs", 25, False),
                ("delivery", 32, False), ("payment", 40, False),
            ]:
                m.OrderMilestone.objects.get_or_create(
                    order=order, kind=kind,
                    defaults=dict(
                        planned_date=days(off),
                        actual_date=days(off) if done else None,
                        status="done" if done else "pending",
                        responsible=users["ivanov"]))
            m.OrderChange.objects.create(
                order=order, change_type="dates",
                before="отгрузка 10.11", after="отгрузка 15.11",
                reason="Задержка комплектующих",
                initiated_by=users["wang"],
                approved_by=users["ivanov"])

        heading("Логистика (Z)")
        ship = m.Shipment.objects.filter(order=order,
                                         container_no="MSKU0012345").first()
        if ship is None:
            ship = m.Shipment.objects.create(
                order=order, qty=Decimal("30.000"),
                weight_kg=Decimal("555.00"), volume_m3=Decimal("8.100"),
                ship_date=days(-2), container_no="MSKU0012345")
            created["n"] += 1
            tr, was = m.Transport.objects.get_or_create(
                shipment=ship, defaults=dict(
                    carrier=log_co, mode="rail", lane=lane,
                    waybill_no="RU-RAIL-88421",
                    cost=Decimal("1250.00")))
            created["n"] += int(was)
            for t_off, place, st in [
                (-2, "Харбин, сортировочная станция", "Отправлен"),
                (-1, "Забайкальск, приграничный парк", "Пограничный переход"),
                (0, "Забайкальск, таможенный пост", "Таможенное оформление"),
            ]:
                m.TrackPoint.objects.get_or_create(
                    transport=tr, event_time=timezone.now()
                    + timedelta(days=t_off),
                    defaults=dict(place=place, status=st))
            m.Incident.objects.create(
                shipment=ship, kind="customs", severity="medium",
                description="Задержана досмотром: нет оригинала "
                            "декларации о происхождении",
                reported_by=users["petrov"], status="in_progress")

        heading("Документы (D)")
        dt_inv = get(m.DocType, "тип", dict(name_ru="Инвойс",
                                            name_zh="发票",
                                            stage="shipment"), code="INV")
        dt_packing = get(m.DocType, "тип",
                         dict(name_ru="Упаковочный лист", name_zh="装箱单",
                              stage="shipment"), code="PL")
        dt_orig = get(m.DocType, "тип",
                      dict(name_ru="Сертификат происхождения",
                           name_zh="原产地证", stage="customs"), code="CO")
        for dt, issuer, vf in [(dt_inv, "Hangzhou Kangtai", True),
                               (dt_packing, "Hangzhou Kangtai", True)]:
            m.Document.objects.get_or_create(
                doc_type=dt, order=order, shipment=ship,
                issuer=issuer, issued_date=days(-3),
                defaults=dict(status="uploaded",
                              file=f"docs/demo/{dt.code.lower()}-demo.pdf"))
        m.Document.objects.get_or_create(
            doc_type=dt_orig, order=order,
            issuer="CCPIT Zhejiang", issued_date=days(-30),
            valid_until=days(10), status="uploaded",
            file="docs/demo/co-form-a-demo.pdf")
        cert = get(m.Certificate, "сертификат",
                   dict(kind="conformity", good=good,
                        issuer="Росаккредитация (ФГИС)",
                        issued_date=days(-300), valid_until=days(21),
                        fgis_no="RA-RU-0345-26",
                        qr_data="RA-RU-0345-26/IKT150"),
                   number="RA-RU-0345-26")
        for dt, st in [(dt_inv, "checked"), (dt_packing, "provided"),
                       (dt_orig, "missing")]:
            m.DocRequirement.objects.get_or_create(
                order=order, doc_type=dt, defaults=dict(status=st))
        m.ComplianceCheck.objects.get_or_create(
            order=order, result="issues", checker=users["ivanov"],
            note="Нет оригинала сертификата происхождения")
        m.DeadlineReminder.objects.get_or_create(
            target_kind="certificate", target_id=cert.id,
            recipient=users["ivanov"],
            defaults=dict(due_date=days(21), status="pending"))

        heading("Коммуникация (K)")
        dialog = m.Dialog.objects.filter(subject_kind="order",
                                         subject_id=order.id).first()
        if dialog is None:
            dialog = m.Dialog.objects.create(
                subject_kind="order", subject_id=order.id,
                subject_label=order.number,
                last_message_at=timezone.now())
            created["n"] += 1
            dialog.participants.add(users["ivanov"], users["wang"])
            msg = m.Message.objects.create(
                dialog=dialog, author=users["ivanov"],
                body="Пришлите, пожалуйста, оригинал сертификата "
                     "происхождения до прибытия на пост.",
                language="ru")
            m.Translation.objects.get_or_create(
                message=msg, target_language="zh",
                defaults=dict(source_language="ru", engine="demo",
                              text="请在到达海关前提供原产地证原件。"))

        heading("Задачи (A)")
        task = m.Task.objects.filter(title__startswith="Получить оригинал").first()
        if task is None:
            task = m.Task.objects.create(
                title="Получить оригинал сертификата происхождения",
                source_kind="order", source_id=order.id,
                assignee=users["ivanov"], due_date=days(3),
                priority="high", status="in_progress")
            created["n"] += 1
            m.TaskReminder.objects.get_or_create(
                task=task, channel="email",
                send_at=timezone.now() + timedelta(days=2))
        m.NotificationSetting.objects.get_or_create(
            user=users["ivanov"], event="doc_expiring", channel="email")
        m.Notification.objects.get_or_create(
            recipient=users["ivanov"], kind="incident_new",
            title="Инцидент на таможенном посту",
            body="Партия MSKU0012345 задержана досмотром",
            link="/exceptions/")

        m.Metric.objects.get_or_create(
            code="orders_active",
            defaults=dict(name_ru="Активные заказы", name_zh="在执行订单",
                          formula="count(status in confirmed..shipped)",
                          unit="шт.", period="month"))
        m.MetricSnapshot.objects.get_or_create(
            metric_id=m.Metric.objects.get(code="orders_active").pk,
            period_key=TODAY.strftime("%Y-%m"),
            defaults=dict(value=Decimal("1"), calculated_at=TODAY))
        m.ComplianceRisk.objects.get_or_create(
            order=order, kind="missing_original_cert",
            defaults=dict(probability="high", impact="high",
                          level="high",
                          advice="Запросить дубликат через CCPIT"))

        heading("Расчёты (A)")
        stmt = m.Statement.objects.filter(order=order).first()
        if stmt is None:
            stmt = m.Statement.objects.create(
                order=order, currency=cny, amount=Decimal("10800.00"),
                due_date=days(20), status="issued",
                confirmed_by=users["petrov"])
            created["n"] += 1
            m.StatementLine.objects.create(
                statement=stmt, description="Поставка ИКТ-150, 60 шт.",
                qty=Decimal("60.000"), price=Decimal("180.00"),
                source="order")
            m.StatementLine.objects.create(
                statement=stmt, description="Ж/д перевозка",
                qty=Decimal("1"), price=Decimal("1250.00"),
                source="transport")
            m.Payment.objects.get_or_create(
                statement=stmt, amount=Decimal("3240.00"),
                defaults=dict(paid_date=days(-18),
                              channel_note="Аккредитив, аванс 30%",
                              buyer_confirmed=True))
        m.Reconciliation.objects.get_or_create(
            order=order, partner=cn_co.name_ru,
            period=TODAY.strftime("%Y-%m"),
            defaults=dict(our_amount=Decimal("3240.00"),
                          partner_amount=Decimal("3240.00"),
                          status="resolved"))

        heading("Системные (S)")
        m.AuditLog.objects.get_or_create(
            actor=admin_u, action="seed_demo", target_kind="system",
            target_id="0",
            defaults=dict(after="Демонстрационные данные созданы",
                          ip_address="127.0.0.1"))
        m.SystemParam.objects.get_or_create(
            key="reminders.days_before_expiry",
            defaults=dict(value="30",
                          note="За сколько дней напоминать об истечении"))

        log("\nГотово: создано записей — " + str(created["n"]) + ".")
        log("Демонстрационные пользователи: ivanov / wang / petrov,"
            " admin; пароль: " + DEMO_PASSWORD)
