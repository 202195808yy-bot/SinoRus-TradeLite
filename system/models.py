# -*- coding: utf-8 -*-
"""系统管理领域（模块 M11）。
审计日志与系统参数。

本模块由 ``<app>/models.py`` 按限界上下文拆分而来；
模型的 ``Meta.db_table`` 显式钉住历史物理表名
（``portal_*``），因此数据库结构、索引名与文档中的
表名清单保持不变。
"""

from django.conf import settings
from django.db import models
from core.i18n import label


class AuditLog(models.Model):
    """操作日志记录（管理）。"""

    actor = models.ForeignKey(settings.AUTH_USER_MODEL,
                              verbose_name="субъект",
                              on_delete=models.SET_NULL, null=True,
                              related_name="audit_entries")
    action = models.CharField("действие", max_length=64)
    target_kind = models.CharField("тип объекта", max_length=32)
    target_id = models.CharField("код объекта", max_length=32)
    before = models.TextField("до изменения", blank=True)
    after = models.TextField("после изменения", blank=True)
    ip_address = models.GenericIPAddressField("IP-адрес", null=True,
                                              blank=True)
    created_at = models.DateTimeField("событие", auto_now_add=True)

    class Meta:
        db_table = "portal_auditlog"
        verbose_name = "запись журнала"
        verbose_name_plural = "журнал действий"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["target_kind", "created_at"])]

    def __str__(self):
        who = self.actor.get_username() if self.actor else label("система")
        return f"{who}: {self.action} {self.target_kind}#{self.target_id}"


class SystemParam(models.Model):
    """由管理员编辑的系统参数。"""

    key = models.SlugField("ключ", max_length=64, unique=True)
    value = models.TextField("значение")
    note = models.CharField("назначение", max_length=191, blank=True)
    updated_at = models.DateTimeField("изменён", auto_now=True)

    class Meta:
        db_table = "portal_systemparam"
        verbose_name = "параметр системы"
        verbose_name_plural = "параметры системы"
        ordering = ["key"]

    def __str__(self):
        return self.key

__all__ = [
    "AuditLog", "SystemParam",
]
