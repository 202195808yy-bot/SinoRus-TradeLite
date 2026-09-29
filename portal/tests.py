# -*- coding: utf-8 -*-
"""Модельные тесты этапа 3.

Проверяют: генерацию номеров, вычисляемые свойства и свойства-доли,
ограничения целостности (``UniqueConstraint`` / ``CheckConstraint``),
валидаторы, покрытие админ-панели и идемпотентность демо-данных.
"""

from datetime import timedelta
from decimal import Decimal

from django.apps import apps
from django.contrib import admin
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from portal import models as m


def make_basic():
    """Создать минимальный набор объектов для тестов."""
    cny, _ = m.Currency.objects.get_or_create(
        code="CNY", defaults=dict(name_ru="Юань", name_zh="人民币",
                                  symbol="¥"))
    ru, _ = m.Country.objects.get_or_create(
        code2="RU", defaults=dict(name_ru="Россия", name_zh="俄罗斯"))
    cn, _ = m.Country.objects.get_or_create(
        code2="CN", defaults=dict(name_ru="Китай", name_zh="中国"))
    pcs, _ = m.Uom.objects.get_or_create(
        code="pcs", defaults=dict(name_ru="штука", name_zh="件"))
    cat, _ = m.GoodCategory.objects.get_or_create(
        code="T", defaults=dict(name_ru="Тест", name_zh="测试"))
    ent_a, _ = m.Enterprise.objects.get_or_create(
        name_ru="Закупщик ТЕСТ",
        defaults=dict(tin="1234567890", country=ru))
    ent_b, _ = m.Enterprise.objects.get_or_create(
        name_ru="Поставщик ТЕСТ",
        defaults=dict(tin="0987654321", country=cn))
    good, _ = m.Good.objects.get_or_create(
        sku="TEST-001",
        defaults=dict(name_ru="Тестовый товар", name_zh="测试商品",
                      category=cat, uom=pcs))
    return cny, ent_a, ent_b, good


class NumberingTest(TestCase):
    def setUp(self):
        self.cny, self.buyer, self.supplier, self.good = make_basic()

    def _rfq(self):
        return m.Rfq.objects.create(
            buyer=self.buyer, title="Тест", due_date=timezone.localdate(),
            currency=self.cny)

    def test_rfq_number_generated(self):
        rfq = self._rfq()
        year = timezone.now().year
        self.assertRegex(
            rfq.number, rf"^RFQ-{year}-\d{{4}}$")

    def test_rfq_number_not_regenerated_on_update(self):
        rfq = self._rfq()
        rfq.title = "Тест 2"
        rfq.save()
        self.assertRegex(rfq.number, r"^RFQ-\d{4}-\d{4}$")

    def test_order_numbers_unique_across_models(self):
        """Номера разных видов документов не пересекаются по префиксу."""
        rfq = self._rfq()
        quote = m.Quote.objects.create(
            rfq=rfq, supplier=self.supplier,
            valid_until=timezone.localdate(), incoterm="FCA",
            currency=self.cny)
        self.assertNotEqual(rfq.number[:3], quote.number[:3])


class ComputedPropertiesTest(TestCase):
    def setUp(self):
        self.cny, self.buyer, self.supplier, self.good = make_basic()
        self.rfq = m.Rfq.objects.create(
            buyer=self.buyer, title="Тест", due_date=timezone.localdate(),
            currency=self.cny)
        self.quote = m.Quote.objects.create(
            rfq=self.rfq, supplier=self.supplier,
            valid_until=timezone.localdate(), incoterm="FCA",
            currency=self.cny)

    def test_line_amounts(self):
        qline = m.QuoteLine.objects.create(
            quote=self.quote, good=self.good,
            qty=Decimal("2.500"), price=Decimal("11.11"))
        self.assertEqual(qline.amount, Decimal("27.78"))
        order = m.Order.objects.create(
            buyer=self.buyer, supplier=self.supplier, quote=self.quote,
            incoterm="FCA", currency=self.cny, amount=Decimal("27.78"))
        oline = m.OrderLine.objects.create(
            order=order, good=self.good, qty=Decimal("3.000"),
            price=Decimal("10.00"))
        self.assertEqual(oline.amount, Decimal("30.00"))

    def test_shipped_share(self):
        order = m.Order.objects.create(
            buyer=self.buyer, supplier=self.supplier, quote=self.quote,
            incoterm="FCA", currency=self.cny, amount=Decimal("100.00"))
        m.OrderLine.objects.create(order=order, good=self.good,
                                   qty=Decimal("60.000"),
                                   price=Decimal("10.00"))
        self.assertEqual(order.shipped_share, Decimal("0"))
        m.Shipment.objects.create(order=order, qty=Decimal("30.000"))
        self.assertEqual(order.shipped_share, Decimal("0.500"))

    def test_reconciliation_diff(self):
        order = m.Order.objects.create(
            buyer=self.buyer, supplier=self.supplier, quote=self.quote,
            incoterm="FCA", currency=self.cny, amount=Decimal("100.00"))
        rec = m.Reconciliation.objects.create(
            order=order, partner="Партнёр", period="2026-09",
            our_amount=Decimal("100.00"),
            partner_amount=Decimal("88.00"))
        self.assertEqual(rec.diff, Decimal("12.00"))

    def test_certificate_expiry_window(self):
        today = timezone.localdate()
        cert = m.Certificate.objects.create(
            number="TEST-CERT-1", kind="conformity", good=self.good,
            issuer="Тест", issued_date=today - timedelta(days=100),
            valid_until=today + timedelta(days=15))
        self.assertTrue(cert.expires_soon)
        cert.valid_until = today + timedelta(days=200)
        self.assertFalse(cert.expires_soon)
        cert.valid_until = today - timedelta(days=1)
        self.assertFalse(cert.expires_soon)

    def test_task_overdue(self):
        today = timezone.localdate()
        task = m.Task.objects.create(
            title="Просроченная", due_date=today - timedelta(days=1),
            status="in_progress")
        self.assertTrue(task.is_overdue)
        task.status = "done"
        self.assertFalse(task.is_overdue)
        task.due_date = today + timedelta(days=5)
        task.status = "new"
        self.assertFalse(task.is_overdue)

    def test_invitation_validity(self):
        today = timezone.localdate()
        ent = m.Enterprise.objects.get(name_ru="Закупщик ТЕСТ")
        inv = m.Invitation.objects.create(
            code="TEST-CODE-1", email="a@b.local", enterprise=ent,
            role="finance", valid_until=today + timedelta(days=7))
        self.assertTrue(inv.is_valid)
        inv.valid_until = today - timedelta(days=1)
        self.assertFalse(inv.is_valid)
        inv.valid_until = today + timedelta(days=7)
        inv.status = "accepted"
        self.assertFalse(inv.is_valid)


class ConstraintTest(TestCase):
    def setUp(self):
        self.cny, self.buyer, self.supplier, self.good = make_basic()

    def test_membership_unique(self):
        user = User.objects.create_user("u1")
        ent = m.Enterprise.objects.get(name_ru="Закупщик ТЕСТ")
        m.Membership.objects.create(user=user, enterprise=ent, role="buyer")
        with self.assertRaises(IntegrityError), transaction.atomic():
            m.Membership.objects.create(user=user, enterprise=ent,
                                        role="finance")

    def test_order_buyer_must_differ_from_supplier(self):
        rfq = m.Rfq.objects.create(
            buyer=self.buyer, title="Т", due_date=timezone.localdate(),
            currency=self.cny)
        quote = m.Quote.objects.create(
            rfq=rfq, supplier=self.supplier,
            valid_until=timezone.localdate(), currency=self.cny)
        with self.assertRaises(IntegrityError), transaction.atomic():
            m.Order.objects.create(
                buyer=self.buyer, supplier=self.buyer, quote=quote,
                currency=self.cny, amount=Decimal("1.00"))

    def test_positive_quantity_enforced(self):
        rfq = m.Rfq.objects.create(
            buyer=self.buyer, title="Т", due_date=timezone.localdate(),
            currency=self.cny)
        with self.assertRaises(IntegrityError), transaction.atomic():
            m.RfqLine.objects.create(rfq=rfq, good=self.good,
                                     qty=Decimal("0.000"))

    def test_document_validity_not_inverted(self):
        dt, _ = m.DocType.objects.get_or_create(
            code="TEST", defaults=dict(name_ru="Тест", name_zh="测试",
                                       stage="order"))
        today = timezone.localdate()
        with self.assertRaises(IntegrityError), transaction.atomic():
            m.Document.objects.create(
                doc_type=dt, file="docs/x.pdf", issued_date=today,
                valid_until=today - timedelta(days=1))

    def test_good_category_level_range(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            m.GoodCategory.objects.create(code="L9", name_ru="Т",
                                          name_zh="测试", level=9)


class ValidatorTest(TestCase):
    def test_good_sku_pattern(self):
        _, _, _, _ = make_basic()
        cat = m.GoodCategory.objects.get(code="T")
        uom = m.Uom.objects.get(code="pcs")
        bad = m.Good(sku="плохой sku", name_ru="Т", name_zh="测试",
                     category=cat, uom=uom)
        with self.assertRaises(ValidationError):
            bad.full_clean()
        ok = m.Good(sku="OK-SKU-2", name_ru="Т", name_zh="测试",
                    category=cat, uom=uom)
        ok.full_clean()

    def test_profile_phone_pattern(self):
        user = User.objects.create_user("u2")
        bad = m.Profile(user=user, phone="не номер")
        with self.assertRaises(ValidationError):
            bad.full_clean()


class AdminCoverageTest(TestCase):
    """Каждая модель видна в администраторе: самостоятельно или как
    инлайн составной сущности."""

    def _inline_models(self):
        result = set()
        for model_admin in admin.site._registry.values():
            for inline_cls in getattr(model_admin, "inlines", []):
                if getattr(inline_cls, "model", None):
                    result.add(inline_cls.model)
        return result

    def test_all_portal_models_visible_in_admin(self):
        concrete = [
            model for model in apps.get_models()
            if model._meta.app_label == "portal"
        ]
        missing = [
            model.__name__ for model in concrete
            if model not in admin.site._registry
            and model not in self._inline_models()
        ]
        self.assertEqual(missing, [])

    def test_audit_log_is_immutable(self):
        audit_admin = admin.site._registry[m.AuditLog]
        self.assertFalse(audit_admin.has_add_permission(None))
        self.assertFalse(audit_admin.has_change_permission(None))


class SeedDemoTest(TestCase):
    """Демо-сценарий строится целиком и идемпотентен."""

    def test_seed_and_idempotency(self):
        call_command("seed_demo", verbosity=0)
        first_orders = m.Order.objects.count()
        self.assertGreaterEqual(first_orders, 1)
        call_command("seed_demo", verbosity=0)
        self.assertEqual(m.Order.objects.count(), first_orders)

    def test_seed_business_chain_integrity(self):
        call_command("seed_demo", verbosity=0)
        order = m.Order.objects.select_related("quote", "buyer",
                                              "supplier").first()
        self.assertIsNotNone(order)
        self.assertTrue(order.quote.rfq.buyer)
        self.assertGreaterEqual(order.lines.count(), 1)
        self.assertGreaterEqual(order.milestones.count(), 8)
        shipment = order.shipments.first()
        self.assertIsNotNone(shipment)
        self.assertIsNotNone(shipment.transport)
        self.assertGreaterEqual(
            shipment.transport.track_points.count(), 1)
        dialog = m.Dialog.objects.get(subject_kind="order",
                                      subject_id=order.id)
        message = dialog.messages.first()
        self.assertIsNotNone(message.translations.first())
