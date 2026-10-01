# -*- coding: utf-8 -*-
"""结算与对账领域（模块 M10）。
账单、账单明细、对账记录与付款登记。

本模块由 ``<app>/models.py`` 按限界上下文拆分而来；
模型的 ``Meta.db_table`` 显式钉住历史物理表名
（``portal_*``），因此数据库结构、索引名与文档中的
表名清单保持不变。
"""

from decimal import Decimal
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone
from core.models import DocNumberMixin, TimeStampedModel
from catalog.models import Currency
from trading.models import Order


class Statement(DocNumberMixin, TimeStampedModel):
    """订单付款账单。"""

    number_prefix = "STM"

    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        ISSUED = "issued", "Выставлен"
        PARTIALLY_PAID = "partial", "Частично оплачен"
        PAID = "paid", "Оплачен"
        DISPUTED = "disputed", "Оспаривается"

    number = models.CharField("номер", max_length=24, unique=True,
                              blank=True)
    order = models.ForeignKey(Order, verbose_name="заказ",
                              on_delete=models.PROTECT,
                              related_name="statements")
    currency = models.ForeignKey(Currency, verbose_name="валюта",
                                 on_delete=models.PROTECT,
                                 related_name="statements")
    amount = models.DecimalField("сумма", max_digits=14, decimal_places=2)
    due_date = models.DateField("срок оплаты", null=True, blank=True)
    status = models.CharField("статус", max_length=16,
                              choices=Status.choices,
                              default=Status.DRAFT)
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="подтвердил",
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="statements_confirmed")

    class Meta:
        db_table = "portal_statement"
        verbose_name = "счёт"
        verbose_name_plural = "счета"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(check=Q(amount__gte=Decimal("0")),
                                   name="statement_amount_non_negative"),
        ]

    def __str__(self):
        return f"{self.number} ({self.order.number})"


class StatementLine(models.Model):
    """结算单据行项。"""

    class Source(models.TextChoices):
        ORDER = "order", "Заказ"
        TRANSPORT = "transport", "Перевозка"
        DUTY = "duty", "Таможня"
        OTHER = "other", "Прочее"

    statement = models.ForeignKey(Statement, verbose_name="счёт",
                                  on_delete=models.CASCADE,
                                  related_name="lines")
    description = models.CharField("назначение платежа", max_length=191)
    qty = models.DecimalField("количество", max_digits=12,
                              decimal_places=3, default=Decimal("1"))
    price = models.DecimalField("цена", max_digits=12, decimal_places=2)
    source = models.CharField("источник", max_length=16,
                              choices=Source.choices, default=Source.ORDER)

    class Meta:
        db_table = "portal_statementline"
        verbose_name = "строка счёта"
        verbose_name_plural = "строки счетов"
        ordering = ["statement", "pk"]
        constraints = [
            models.CheckConstraint(
                check=Q(qty__gt=Decimal("0"), price__gte=Decimal("0")),
                name="statementline_values_positive"),
        ]

    @property
    def amount(self):
        return (self.qty * self.price).quantize(Decimal("0.01"))

    def __str__(self):
        return f"{self.description}: {self.amount}"


class Reconciliation(models.Model):
    """周期内与交易对手的对账。"""

    class Status(models.TextChoices):
        NEW = "new", "Начата"
        IN_PROGRESS = "in_progress", "В работе"
        RESOLVED = "resolved", "Сверена"

    order = models.ForeignKey(Order, verbose_name="заказ",
                              on_delete=models.PROTECT,
                              related_name="reconciliations")
    partner = models.CharField("контрагент", max_length=128)
    period = models.CharField("период", max_length=16,
                              help_text="Например: 2026-09")
    our_amount = models.DecimalField("наша сумма", max_digits=14,
                                     decimal_places=2)
    partner_amount = models.DecimalField("сумма партнёра", max_digits=14,
                                         decimal_places=2)
    diff = models.DecimalField("разница", max_digits=14, decimal_places=2,
                               default=Decimal("0"))
    status = models.CharField("статус", max_length=16,
                              choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField("создано", auto_now_add=True)

    class Meta:
        db_table = "portal_reconciliation"
        verbose_name = "сверка расчётов"
        verbose_name_plural = "сверки расчётов"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.partner} {self.period}"

    def save(self, *args, **kwargs):
        self.diff = self.our_amount - self.partner_amount
        super().save(*args, **kwargs)


class Payment(models.Model):
    """账单付款登记（平台外付款）。"""

    statement = models.ForeignKey(Statement, verbose_name="счёт",
                                  on_delete=models.PROTECT,
                                  related_name="payments")
    paid_date = models.DateField("дата регистрации", default=timezone.now)
    amount = models.DecimalField("сумма", max_digits=14, decimal_places=2)
    channel_note = models.CharField("канал и реквизиты", max_length=191,
                                    blank=True)
    buyer_confirmed = models.BooleanField("подтвердил закупщик",
                                          default=False)
    supplier_confirmed = models.BooleanField("подтвердил поставщик",
                                             default=False)
    created_at = models.DateTimeField("создано", auto_now_add=True)

    class Meta:
        db_table = "portal_payment"
        verbose_name = "регистрация платежа"
        verbose_name_plural = "регистрации платежей"
        ordering = ["-paid_date"]
        constraints = [
            models.CheckConstraint(check=Q(amount__gt=Decimal("0")),
                                   name="payment_amount_positive"),
        ]

    def __str__(self):
        return f"{self.statement.number}: {self.amount}"

    @property
    def is_confirmed(self):
        return self.buyer_confirmed and self.supplier_confirmed

__all__ = [
    "Statement", "StatementLine", "Reconciliation",
    "Payment",
]
