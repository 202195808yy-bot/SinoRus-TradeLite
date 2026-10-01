# -*- coding: utf-8 -*-
"""单证与合规领域（模块 M6）。
单证类型、已登记单证、证书、单证要求、合规自查与期限提醒。

本模块由 ``<app>/models.py`` 按限界上下文拆分而来；
模型的 ``Meta.db_table`` 显式钉住历史物理表名
（``portal_*``），因此数据库结构、索引名与文档中的
表名清单保持不变。
"""

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone
from core.models import TimeStampedModel
from catalog.models import Good
from logistics.models import Shipment
from trading.models import Order


class DocType(models.Model):
    """单证类型字典。"""

    class Stage(models.TextChoices):
        ORDER = "order", "Заказ"
        PRODUCTION = "production", "Производство"
        SHIPMENT = "shipment", "Отгрузка"
        CUSTOMS = "customs", "Таможня"
        PAYMENT = "payment", "Расчёт"

    code = models.CharField("код", max_length=16, unique=True)
    name_ru = models.CharField("название (рус.)", max_length=128)
    name_zh = models.CharField("название (кит.)", max_length=128)
    stage = models.CharField("обязателен на этапе", max_length=16,
                             choices=Stage.choices)

    class Meta:
        db_table = "portal_doctype"
        verbose_name = "тип документа"
        verbose_name_plural = "типы документов"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name_ru}"


class Document(TimeStampedModel):
    """交易单证（发票、提单等）。"""

    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        SIGNED = "signed", "Подписан"
        UPLOADED = "uploaded", "Загружен"
        ARCHIVED = "archived", "В архиве"
        EXPIRED = "expired", "Просрочен"

    doc_type = models.ForeignKey(DocType, verbose_name="тип документа",
                                 on_delete=models.PROTECT,
                                 related_name="documents")
    order = models.ForeignKey(Order, verbose_name="заказ",
                              on_delete=models.PROTECT, null=True, blank=True,
                              related_name="documents")
    shipment = models.ForeignKey(Shipment, verbose_name="партия",
                                 on_delete=models.PROTECT, null=True,
                                 blank=True, related_name="documents")
    file = models.FileField("файл", upload_to="docs/%Y/%m")
    issuer = models.CharField("кем выдан", max_length=128, blank=True)
    issued_date = models.DateField("дата выдачи")
    valid_until = models.DateField("действителен до", null=True, blank=True)
    status = models.CharField("статус", max_length=16,
                              choices=Status.choices,
                              default=Status.UPLOADED)

    class Meta:
        db_table = "portal_document"
        verbose_name = "документ"
        verbose_name_plural = "документы"
        ordering = ["-issued_date"]
        indexes = [models.Index(fields=["status", "valid_until"])]
        constraints = [
            models.CheckConstraint(
                check=Q(valid_until__isnull=True)
                      | Q(valid_until__gte=models.F("issued_date")),
                name="document_validity_not_inverted"),
        ]

    def __str__(self):
        return f"{self.doc_type.code} ({self.issued_date})"


class Certificate(TimeStampedModel):
    """许可文件 / 证书。"""

    class Kind(models.TextChoices):
        CONFORMITY = "conformity", "Соответствия"
        ORIGIN = "origin", "Происхождения"
        PHYTO = "phyto", "Карантинный"
        QUALITY = "quality", "Качества"

    number = models.CharField("номер", max_length=32, unique=True)
    kind = models.CharField("вид", max_length=16, choices=Kind.choices)
    good = models.ForeignKey(Good, verbose_name="товар",
                             on_delete=models.PROTECT,
                             related_name="certificates")
    issuer = models.CharField("орган выдачи", max_length=128)
    issued_date = models.DateField("дата выдачи")
    valid_until = models.DateField("действителен до")
    fgis_no = models.CharField("регистрация в ФГИС", max_length=32,
                               blank=True)
    qr_data = models.CharField("данные QR-кода", max_length=128, blank=True)

    class Meta:
        db_table = "portal_certificate"
        verbose_name = "сертификат"
        verbose_name_plural = "сертификаты"
        ordering = ["valid_until"]

    def __str__(self):
        return f"{self.kind}: {self.number}"

    @property
    def days_to_expiry(self):
        return (self.valid_until - timezone.now().date()).days

    @property
    def expires_soon(self):
        return 0 <= self.days_to_expiry <= 30


class DocRequirement(models.Model):
    """成套单证：要求与齐备标记。"""

    class Status(models.TextChoices):
        MISSING = "missing", "Отсутствует"
        PROVIDED = "provided", "Предоставлен"
        CHECKED = "checked", "Проверен"

    order = models.ForeignKey(Order, verbose_name="заказ",
                              on_delete=models.CASCADE,
                              related_name="doc_requirements")
    doc_type = models.ForeignKey(DocType, verbose_name="тип документа",
                                 on_delete=models.PROTECT,
                                 related_name="requirements")
    status = models.CharField("статус", max_length=16,
                              choices=Status.choices,
                              default=Status.MISSING)
    document = models.ForeignKey(
        Document, verbose_name="загруженный документ",
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="used_in_requirements")
    note = models.CharField("примечание", max_length=191, blank=True)

    class Meta:
        db_table = "portal_docrequirement"
        verbose_name = "требование к комплекту"
        verbose_name_plural = "требования к комплекту"
        ordering = ["order", "doc_type"]
        constraints = [
            models.UniqueConstraint(fields=["order", "doc_type"],
                                    name="docrequirement_unique"),
        ]

    def __str__(self):
        return f"{self.order.number}: {self.doc_type.code}"


class ComplianceCheck(models.Model):
    """对照要求的合规自查结果。"""

    class Result(models.TextChoices):
        PASSED = "passed", "Пройдена"
        ISSUES = "issues", "Есть замечания"
        FAILED = "failed", "Не пройдена"

    order = models.ForeignKey(Order, verbose_name="заказ",
                              on_delete=models.CASCADE,
                              related_name="compliance_checks")
    checked_at = models.DateTimeField("проверено", auto_now_add=True)
    result = models.CharField("результат", max_length=16,
                              choices=Result.choices)
    checker = models.ForeignKey(settings.AUTH_USER_MODEL,
                                verbose_name="проверяющий",
                                on_delete=models.SET_NULL, null=True,
                                related_name="compliance_checks")
    note = models.TextField("замечания", blank=True)

    class Meta:
        db_table = "portal_compliancecheck"
        verbose_name = "проверка соответствия"
        verbose_name_plural = "проверки соответствия"
        ordering = ["-checked_at"]

    def __str__(self):
        return f"{self.order.number}: {self.result}"


class DeadlineReminder(models.Model):
    """单证或证书的有效期提醒。"""

    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает"
        SENT = "sent", "Отправлено"
        ACKED = "acked", "Подтверждено"
        CANCELED = "canceled", "Отменено"

    target_kind = models.CharField("вид объекта", max_length=16)
    target_id = models.PositiveBigIntegerField("код объекта")
    due_date = models.DateField("напоминание о дате")
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  verbose_name="получатель",
                                  on_delete=models.CASCADE,
                                  related_name="deadline_reminders")
    sent_at = models.DateTimeField("отправлено", null=True, blank=True)
    status = models.CharField("статус", max_length=16,
                              choices=Status.choices,
                              default=Status.PENDING)

    class Meta:
        db_table = "portal_deadlinereminder"
        verbose_name = "напоминание о сроке"
        verbose_name_plural = "напоминания о сроках"
        ordering = ["due_date"]

    def __str__(self):
        return f"{self.target_kind}#{self.target_id}: {self.due_date}"

__all__ = [
    "DocType", "Document", "Certificate",
    "DocRequirement", "ComplianceCheck", "DeadlineReminder",
]
