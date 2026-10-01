# -*- coding: utf-8 -*-
"""双语沟通领域（模块 M7）。
按业务对象组织的会话、消息、机器译文与附件。

本模块由 ``<app>/models.py`` 按限界上下文拆分而来；
模型的 ``Meta.db_table`` 显式钉住历史物理表名
（``portal_*``），因此数据库结构、索引名与文档中的
表名清单保持不变。
"""

from django.conf import settings
from django.db import models
from core.i18n import label


class Dialog(models.Model):
    """绑定到业务对象的双语对话。"""

    class SubjectKind(models.TextChoices):
        RFQ = "rfq", "Запрос"
        QUOTE = "quote", "Предложение"
        ORDER = "order", "Заказ"
        SHIPMENT = "shipment", "Партия"
        INCIDENT = "incident", "Инцидент"

    class Status(models.TextChoices):
        OPEN = "open", "Открыт"
        CLOSED = "closed", "Закрыт"

    subject_kind = models.CharField("тип объекта", max_length=16,
                                    choices=SubjectKind.choices)
    subject_id = models.PositiveBigIntegerField("код объекта")
    subject_label = models.CharField("обозначение объекта", max_length=128,
                                     blank=True)
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, verbose_name="участники",
        related_name="dialogs")
    status = models.CharField("статус", max_length=8,
                              choices=Status.choices, default=Status.OPEN)
    last_message_at = models.DateTimeField("последнее сообщение",
                                           null=True, blank=True)

    class Meta:
        db_table = "portal_dialog"
        verbose_name = "диалог"
        verbose_name_plural = "диалоги"
        ordering = ["-last_message_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["subject_kind", "subject_id"],
                name="dialog_subject_unique"),
        ]

    def __str__(self):
        return f"{label('Диалог')}: {self.subject_label or self.subject_id}"


class Message(models.Model):
    """对话参与者的消息。"""

    class Language(models.TextChoices):
        RU = "ru", "Русский"
        ZH = "zh", "中文"

    dialog = models.ForeignKey(Dialog, verbose_name="диалог",
                               on_delete=models.CASCADE,
                               related_name="messages")
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
                               verbose_name="автор",
                               on_delete=models.PROTECT,
                               related_name="messages")
    body = models.TextField("текст")
    language = models.CharField("язык", max_length=2,
                                choices=Language.choices,
                                default=Language.RU)
    created_at = models.DateTimeField("отправлено", auto_now_add=True)

    class Meta:
        db_table = "portal_message"
        verbose_name = "сообщение"
        verbose_name_plural = "сообщения"
        ordering = ["dialog", "created_at"]
        indexes = [models.Index(fields=["dialog", "created_at"])]

    def __str__(self):
        who = self.author.get_username()
        return f"{who}: {self.body[:40]}"


class Translation(models.Model):
    """消息的机器翻译。"""

    message = models.ForeignKey(Message, verbose_name="сообщение",
                                on_delete=models.CASCADE,
                                related_name="translations")
    source_language = models.CharField("исходный язык", max_length=2)
    target_language = models.CharField("язык перевода", max_length=2)
    text = models.TextField("перевод")
    engine = models.CharField("движок перевода", max_length=32,
                              default="manual")
    created_at = models.DateTimeField("создан", auto_now_add=True)

    class Meta:
        db_table = "portal_translation"
        verbose_name = "перевод"
        verbose_name_plural = "переводы"
        ordering = ["message", "target_language"]
        constraints = [
            models.UniqueConstraint(
                fields=["message", "target_language"],
                name="translation_message_target_unique"),
        ]

    def __str__(self):
        return f"{label('Перевод')} #{self.message_id} → {self.target_language}"


class Attachment(models.Model):
    """附加到消息、单证或异常事件的文件。"""

    file = models.FileField("файл", upload_to="attach/%Y/%m")
    owner_kind = models.CharField("тип владельца", max_length=16)
    owner_id = models.PositiveBigIntegerField("код владельца")
    size_bytes = models.BigIntegerField("размер, байт", null=True, blank=True)
    mime_type = models.CharField("MIME-тип", max_length=96, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="загрузил",
        on_delete=models.SET_NULL, null=True, related_name="attachments")
    created_at = models.DateTimeField("загружено", auto_now_add=True)

    class Meta:
        db_table = "portal_attachment"
        verbose_name = "вложение"
        verbose_name_plural = "вложения"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.owner_kind}#{self.owner_id}"

__all__ = [
    "Dialog", "Message", "Translation",
    "Attachment",
]
