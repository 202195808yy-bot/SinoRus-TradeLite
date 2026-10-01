# -*- coding: utf-8 -*-
"""交易领域（模块 M3 + M4）。
询价单、报价单及其版本、订单、订单明细、执行阶段与变更单。

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
from core.models import DocNumberMixin, Incoterm, TimeStampedModel
from accounts.models import Enterprise
from catalog.models import Currency, Good


class Rfq(DocNumberMixin, TimeStampedModel):
    """采购员创建的询价单（RFQ）。"""

    number_prefix = "RFQ"

    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        SENT = "sent", "Опубликован"
        QUOTED = "quoted", "Есть предложения"
        CLOSED = "closed", "Закрыт"
        CANCELED = "canceled", "Отменён"

    number = models.CharField("номер", max_length=24, unique=True,
                              blank=True)
    buyer = models.ForeignKey(Enterprise, verbose_name="закупщик",
                              on_delete=models.PROTECT,
                              related_name="rfqs")
    title = models.CharField("заголовок", max_length=191)
    due_date = models.DateField("срок ответа")
    incoterm = models.CharField("базис поставки", max_length=3,
                                choices=Incoterm.choices,
                                default=Incoterm.FCA)
    currency = models.ForeignKey(Currency, verbose_name="валюта",
                                 on_delete=models.PROTECT,
                                 related_name="rfqs")
    status = models.CharField("статус", max_length=16,
                              choices=Status.choices,
                              default=Status.DRAFT)
    comment = models.TextField("комментарий", blank=True)

    class Meta:
        db_table = "portal_rfq"
        verbose_name = "запрос котировки"
        verbose_name_plural = "запросы котировки"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "due_date"])]

    def __str__(self):
        return f"{self.number}: {self.title}"

    @property
    def is_overdue(self):
        return (self.status in (self.Status.SENT, self.Status.QUOTED)
                and self.due_date < timezone.now().date())


class RfqLine(models.Model):
    """询价单明细行。"""

    rfq = models.ForeignKey(Rfq, verbose_name="запрос",
                            on_delete=models.CASCADE, related_name="lines")
    good = models.ForeignKey(Good, verbose_name="товар",
                             on_delete=models.PROTECT,
                             related_name="rfq_lines")
    qty = models.DecimalField("количество", max_digits=12,
                              decimal_places=3)
    target_price = models.DecimalField(
        "целевая цена", max_digits=12, decimal_places=2,
        null=True, blank=True)
    requirement = models.CharField("требование", max_length=191,
                                   blank=True)

    class Meta:
        db_table = "portal_rfqline"
        verbose_name = "позиция запроса"
        verbose_name_plural = "позиции запросов"
        ordering = ["rfq", "pk"]
        constraints = [
            models.CheckConstraint(check=Q(qty__gt=Decimal("0")),
                                   name="rfqline_qty_positive"),
        ]

    def __str__(self):
        return f"#{self.pk}: {self.good} × {self.qty}"


class Quote(DocNumberMixin, TimeStampedModel):
    """供应商对询价单的报价。"""

    number_prefix = "QUO"

    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        SENT = "sent", "Отправлено"
        ACCEPTED = "accepted", "Принято"
        REJECTED = "rejected", "Отклонено"
        EXPIRED = "expired", "Истекло"
        WITHDRAWN = "withdrawn", "Отозвано"

    number = models.CharField("номер", max_length=24, unique=True,
                              blank=True)
    rfq = models.ForeignKey(Rfq, verbose_name="запрос",
                            on_delete=models.PROTECT, related_name="quotes")
    supplier = models.ForeignKey(Enterprise, verbose_name="поставщик",
                                 on_delete=models.PROTECT,
                                 related_name="quotes")
    valid_until = models.DateField("действительно до")
    incoterm = models.CharField("базис поставки", max_length=3,
                                choices=Incoterm.choices)
    currency = models.ForeignKey(Currency, verbose_name="валюта",
                                 on_delete=models.PROTECT,
                                 related_name="quotes")
    amount = models.DecimalField("сумма", max_digits=14, decimal_places=2,
                                 default=Decimal("0"))
    status = models.CharField("статус", max_length=16,
                              choices=Status.choices,
                              default=Status.DRAFT)
    comment = models.TextField("комментарий", blank=True)

    class Meta:
        db_table = "portal_quote"
        verbose_name = "предложение"
        verbose_name_plural = "предложения"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "valid_until"])]
        constraints = [
            models.CheckConstraint(check=Q(amount__gte=Decimal("0")),
                                   name="quote_amount_non_negative"),
        ]

    def __str__(self):
        return f"{self.number} ({self.supplier})"

    @property
    def is_valid(self):
        return (self.status == self.Status.SENT
                and self.valid_until >= timezone.now().date())


class QuoteLine(models.Model):
    """报价明细行。"""

    quote = models.ForeignKey(Quote, verbose_name="предложение",
                              on_delete=models.CASCADE,
                              related_name="lines")
    good = models.ForeignKey(Good, verbose_name="товар",
                             on_delete=models.PROTECT,
                             related_name="quote_lines")
    qty = models.DecimalField("количество", max_digits=12,
                              decimal_places=3)
    price = models.DecimalField("цена", max_digits=12, decimal_places=2)
    delivery_days = models.PositiveSmallIntegerField(
        "срок поставки, сут", null=True, blank=True)

    class Meta:
        db_table = "portal_quoteline"
        verbose_name = "позиция предложения"
        verbose_name_plural = "позиции предложений"
        ordering = ["quote", "pk"]
        constraints = [
            models.CheckConstraint(
                check=Q(qty__gt=Decimal("0"), price__gte=Decimal("0")),
                name="quoteline_values_positive"),
        ]

    @property
    def amount(self):
        return (self.qty * self.price).quantize(Decimal("0.01"))

    def __str__(self):
        return f"#{self.pk}: {self.good}"


class QuoteVersion(models.Model):
    """固定已变更条款的报价版本。"""

    quote = models.ForeignKey(Quote, verbose_name="предложение",
                              on_delete=models.CASCADE,
                              related_name="versions")
    version = models.PositiveSmallIntegerField("номер версии", default=1)
    changed_fields = models.CharField("изменённые поля", max_length=191,
                                      blank=True)
    comment = models.CharField("пояснение", max_length=256, blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
                               verbose_name="изменил",
                               on_delete=models.SET_NULL, null=True,
                               related_name="quote_versions")
    created_at = models.DateTimeField("создано", auto_now_add=True)

    class Meta:
        db_table = "portal_quoteversion"
        verbose_name = "версия предложения"
        verbose_name_plural = "версии предложений"
        ordering = ["quote", "version"]
        constraints = [
            models.UniqueConstraint(fields=["quote", "version"],
                                    name="quoteversion_unique"),
        ]

    def __str__(self):
        return f"{self.quote.number} v{self.version}"


class Order(DocNumberMixin, TimeStampedModel):
    """已确认的交易——领域的核心。"""

    number_prefix = "ORD"

    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        CONFIRMED = "confirmed", "Подписан"
        IN_PRODUCTION = "in_production", "Производство"
        SHIPPED = "shipped", "Отгружен"
        COMPLETED = "completed", "Завершён"
        CANCELED = "canceled", "Отменён"

    number = models.CharField("номер", max_length=24, unique=True,
                              blank=True)
    buyer = models.ForeignKey(Enterprise, verbose_name="закупщик",
                              on_delete=models.PROTECT,
                              related_name="orders_as_buyer")
    supplier = models.ForeignKey(Enterprise, verbose_name="поставщик",
                                 on_delete=models.PROTECT,
                                 related_name="orders_as_supplier")
    quote = models.ForeignKey(Quote, verbose_name="предложение",
                              on_delete=models.PROTECT,
                              related_name="orders")
    incoterm = models.CharField("базис поставки", max_length=3,
                                choices=Incoterm.choices)
    currency = models.ForeignKey(Currency, verbose_name="валюта",
                                 on_delete=models.PROTECT,
                                 related_name="orders")
    amount = models.DecimalField("сумма", max_digits=14, decimal_places=2)
    status = models.CharField("статус", max_length=16,
                              choices=Status.choices,
                              default=Status.DRAFT)
    signed_date = models.DateField("дата подписания", null=True, blank=True)

    class Meta:
        db_table = "portal_order"
        verbose_name = "заказ"
        verbose_name_plural = "заказы"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "created_at"])]
        constraints = [
            models.CheckConstraint(
                check=~Q(buyer=models.F("supplier")),
                name="order_buyer_differs_supplier"),
            models.CheckConstraint(
                check=Q(amount__gte=Decimal("0")),
                name="order_amount_non_negative"),
        ]

    def __str__(self):
        return f"{self.number}: {self.supplier} → {self.buyer}"

    @property
    def shipped_share(self):
        """已发货批次占订单总批次数的比例。"""
        total = sum(line.qty for line in self.lines.all())
        if not total:
            return Decimal("0")
        shipped = sum(sh.qty for sh in self.shipments.all())
        return (shipped / total).quantize(Decimal("0.001"))


class OrderLine(models.Model):
    """订单条目。"""

    order = models.ForeignKey(Order, verbose_name="заказ",
                              on_delete=models.CASCADE,
                              related_name="lines")
    good = models.ForeignKey(Good, verbose_name="товар",
                             on_delete=models.PROTECT,
                             related_name="order_lines")
    qty = models.DecimalField("количество", max_digits=12,
                              decimal_places=3)
    price = models.DecimalField("цена", max_digits=12, decimal_places=2)
    delivery_days = models.PositiveSmallIntegerField(
        "срок поставки, сут", null=True, blank=True)

    class Meta:
        db_table = "portal_orderline"
        verbose_name = "позиция заказа"
        verbose_name_plural = "позиции заказов"
        ordering = ["order", "pk"]
        constraints = [
            models.CheckConstraint(
                check=Q(qty__gt=Decimal("0"), price__gte=Decimal("0")),
                name="orderline_values_positive"),
        ]

    @property
    def amount(self):
        return (self.qty * self.price).quantize(Decimal("0.01"))

    def __str__(self):
        return f"#{self.pk}: {self.good}"


class OrderMilestone(models.Model):
    """订单执行的阶段（里程碑）。"""

    class Kind(models.TextChoices):
        CONTRACT = "contract", "Подписание"
        PREPAYMENT = "prepayment", "Предоплата"
        PRODUCTION = "production", "Производство"
        PACKING = "packing", "Упаковка"
        SHIPMENT = "shipment", "Отгрузка"
        CUSTOMS = "customs", "Таможня"
        DELIVERY = "delivery", "Передача"
        PAYMENT = "payment", "Расчёт"

    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает"
        DONE = "done", "Выполнен"
        SKIPPED = "skipped", "Пропущен"

    order = models.ForeignKey(Order, verbose_name="заказ",
                              on_delete=models.CASCADE,
                              related_name="milestones")
    kind = models.CharField("вид этапа", max_length=16,
                            choices=Kind.choices)
    planned_date = models.DateField("плановая дата")
    actual_date = models.DateField("фактическая дата", null=True, blank=True)
    status = models.CharField("статус", max_length=16,
                              choices=Status.choices,
                              default=Status.PENDING)
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="ответственный",
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="milestones")

    class Meta:
        db_table = "portal_ordermilestone"
        verbose_name = "этап заказа"
        verbose_name_plural = "этапы заказов"
        ordering = ["order", "planned_date"]
        constraints = [
            models.UniqueConstraint(fields=["order", "kind"],
                                    name="milestone_order_kind_unique"),
        ]

    def __str__(self):
        return f"{self.order.number}: {self.get_kind_display()}"


class OrderChange(models.Model):
    """已记录的订单条件变更。"""

    class ChangeType(models.TextChoices):
        SCOPE = "scope", "Состав"
        DATES = "dates", "Сроки"
        PRICE = "price", "Цена"
        ADDRESS = "address", "Адрес"
        OTHER = "other", "Прочее"

    order = models.ForeignKey(Order, verbose_name="заказ",
                              on_delete=models.CASCADE,
                              related_name="changes")
    change_type = models.CharField("тип изменения", max_length=16,
                                   choices=ChangeType.choices)
    before = models.TextField("было", blank=True)
    after = models.TextField("стало", blank=True)
    reason = models.TextField("причина", blank=True)
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="инициатор",
        on_delete=models.SET_NULL, null=True, related_name="changes_init")
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="согласовал",
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="changes_approved")
    created_at = models.DateTimeField("создано", auto_now_add=True)

    class Meta:
        db_table = "portal_orderchange"
        verbose_name = "изменение заказа"
        verbose_name_plural = "изменения заказов"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order.number}: {self.get_change_type_display()}"

__all__ = [
    "Rfq", "RfqLine", "Quote",
    "QuoteLine", "QuoteVersion", "Order",
    "OrderLine", "OrderMilestone", "OrderChange",
]
