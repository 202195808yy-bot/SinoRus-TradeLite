# -*- coding: utf-8 -*-
"""任务与提醒 在管理后台中的注册。

拆分后每个应用只注册自己的模型；面板的站点标题、
分组与指标卡片分别在 ``core/admin.py``、
``core/admin_site.py``、``core/admin_kpi.py`` 中。
"""

from django.contrib import admin

from . import models as m


@admin.register(m.Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("number", "title", "assignee", "due_date", "priority",
                    "status")
    list_filter = ("status", "priority", "source_kind")
    search_fields = ("number", "title")


@admin.register(m.TaskReminder)
class TaskReminderAdmin(admin.ModelAdmin):
    list_display = ("task", "channel", "send_at", "is_sent")
    list_filter = ("channel", "is_sent")


@admin.register(m.NotificationSetting)
class NotificationSettingAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "channel", "is_enabled")
    list_filter = ("channel", "is_enabled")


@admin.register(m.Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "kind", "title", "is_read", "created_at")
    list_filter = ("kind", "is_read")
    search_fields = ("title",)
