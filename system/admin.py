# -*- coding: utf-8 -*-
"""系统管理 在管理后台中的注册。

拆分后每个应用只注册自己的模型；面板的站点标题、
分组与指标卡片分别在 ``core/admin.py``、
``core/admin_site.py``、``core/admin_kpi.py`` 中。
"""

from django.contrib import admin

from . import models as m
from core.admin_i18n import LazyRu


@admin.register(m.SystemParam)
class SystemParamAdmin(admin.ModelAdmin):
    list_display = ("pk", "display",)
    search_fields = ("pk",)

    def display(self, obj):
        return str(obj)
    display.short_description = LazyRu("значение")


@admin.register(m.AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "action", "target_kind",
                    "target_id")
    list_filter = ("action", "target_kind")

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False
