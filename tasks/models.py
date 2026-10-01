# -*- coding: utf-8 -*-
"""任务与提醒领域（模块 M8）。
任务、任务提醒、通知设置与通知。

本模块由 ``<app>/models.py`` 按限界上下文拆分而来；
模型的 ``Meta.db_table`` 显式钉住历史物理表名
（``portal_*``），因此数据库结构、索引名与文档中的
表名清单保持不变。
"""

from django.conf import settings
from django.db import models
from django.utils import timezone
from core.models import DocNumberMixin, TimeStampedModel


class Task(DocNumberMixin, TimeStampedModel):
    """由领域事件产生的任务。"""

    number_prefix = "TSK"

    class Source(models.TextChoices):
        ORDER = "order", "Заказ"
        RFQ = "rfq", "Запрос"
        DOCUMENT = "document", "Документ"
        INCIDENT = "incident", "Инцидент"
        MANUAL = "manual", "Вручную"

    class Priority(models.TextChoices):
        LOW = "low", "Низкий"
        NORMAL = "normal", "Обычный"
        HIGH = "high", "Высокий"

    class Status(models.TextChoices):
        NEW = "new", "Новая"
        IN_PROGRESS = "in_progress", "В работе"
        DONE = "done", "Выполнена"
        CANCELED = "canceled", "Отменена"

    number = models.CharField("номер", max_length=24, unique=True,
                              blank=True)
    title = models.CharField("заголовок", max_length=191)
    source_kind = models.CharField("источник", max_length=16,
                                   choices=Source.choices,
                                   default=Source.MANUAL)
    source_id = models.PositiveBigIntegerField("код источника", null=True,
                                               blank=True)
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL,
                                 verbose_name="исполнитель",
                                 on_delete=models.SET_NULL, null=True,
                                 blank=True, related_name="tasks")
    due_date = models.DateField("срок", null=True, blank=True)
    priority = models.CharField("приоритет", max_length=8,
                                choices=Priority.choices,
                                default=Priority.NORMAL)
    status = models.CharField("статус", max_length=16,
                              choices=Status.choices, default=Status.NEW)

    class Meta:
        db_table = "portal_task"
        verbose_name = "задача"
        verbose_name_plural = "задачи"
        ordering = ["status", "due_date"]
        indexes = [models.Index(fields=["assignee", "status"])]

    def __str__(self):
        return f"{self.number}: {self.title}"

    @property
    def is_overdue(self):
        return (self.status in (self.Status.NEW, self.Status.IN_PROGRESS)
                and self.due_date is not None
                and self.due_date < timezone.now().date())


class TaskReminder(models.Model):
    """通过所选渠道发送的任务提醒。"""

    class Channel(models.TextChoices):
        IN_APP = "in_app", "В приложении"
        EMAIL = "email", "Электронная почта"
        PUSH = "push", "Push"

    task = models.ForeignKey(Task, verbose_name="задача",
                             on_delete=models.CASCADE,
                             related_name="reminders")
    channel = models.CharField("канал", max_length=8,
                               choices=Channel.choices,
                               default=Channel.IN_APP)
    send_at = models.DateTimeField("время отправки")
    is_sent = models.BooleanField("отправлено", default=False)

    class Meta:
        db_table = "portal_taskreminder"
        verbose_name = "напоминание задачи"
        verbose_name_plural = "напоминания задач"
        ordering = ["send_at"]

    def __str__(self):
        return f"{self.task.number} → {self.get_channel_display()}"


class NotificationSetting(models.Model):
    """规则：按哪个事件、向哪个渠道发送通知。"""

    class Event(models.TextChoices):
        RFQ_ANSWERED = "rfq_answered", "Ответ на запрос"
        QUOTE_CHANGED = "quote_changed", "Изменение предложения"
        ORDER_CHANGED = "order_changed", "Изменение заказа"
        DOC_EXPIRING = "doc_expiring", "Истекает документ"
        INCIDENT_NEW = "incident_new", "Новый инцидент"
        TASK_DUE = "task_due", "Срок задачи"

    class Channel(models.TextChoices):
        IN_APP = "in_app", "В приложении"
        EMAIL = "email", "Электронная почта"
        PUSH = "push", "Push"

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             verbose_name="пользователь",
                             on_delete=models.CASCADE,
                             related_name="notification_settings")
    event = models.CharField("событие", max_length=32,
                             choices=Event.choices)
    channel = models.CharField("канал", max_length=8,
                               choices=Channel.choices,
                               default=Channel.IN_APP)
    is_enabled = models.BooleanField("включено", default=True)

    class Meta:
        db_table = "portal_notificationsetting"
        verbose_name = "настройка уведомления"
        verbose_name_plural = "настройки уведомлений"
        ordering = ["user", "event"]
        constraints = [
            models.UniqueConstraint(fields=["user", "event", "channel"],
                                    name="notifsetting_unique"),
        ]

    def __str__(self):
        return (f"{self.user.get_username()}:"
                f" {self.event} → {self.channel}")


class Notification(models.Model):
    """参与者的个人通知。"""

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  verbose_name="получатель",
                                  on_delete=models.CASCADE,
                                  related_name="notifications")
    kind = models.CharField("тип", max_length=32)
    title = models.CharField("заголовок", max_length=191)
    body = models.TextField("текст", blank=True)
    link = models.CharField("ссылка перехода", max_length=191, blank=True)
    is_read = models.BooleanField("прочитано", default=False)
    created_at = models.DateTimeField("отправлено", auto_now_add=True)

    class Meta:
        db_table = "portal_notification"
        verbose_name = "уведомление"
        verbose_name_plural = "уведомления"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["recipient", "is_read"])]

    def __str__(self):
        return f"{self.recipient.get_username()}: {self.title}"

__all__ = [
    "Task", "TaskReminder", "NotificationSetting",
    "Notification",
]
