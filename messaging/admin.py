# -*- coding: utf-8 -*-
"""双语沟通 在管理后台中的注册。

拆分后每个应用只注册自己的模型；面板的站点标题、
分组与指标卡片分别在 ``core/admin.py``、
``core/admin_site.py``、``core/admin_kpi.py`` 中。
"""

from django.contrib import admin

from . import models as m


@admin.register(m.Dialog)
class DialogAdmin(admin.ModelAdmin):
    list_display = ("subject_kind", "subject_label", "status",
                    "last_message_at")
    list_filter = ("subject_kind", "status")


@admin.register(m.Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("dialog", "author", "language", "created_at")
    list_filter = ("language",)
    search_fields = ("body",)


@admin.register(m.Translation)
class TranslationAdmin(admin.ModelAdmin):
    list_display = ("message", "source_language", "target_language",
                    "engine", "created_at")


@admin.register(m.Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("owner_kind", "owner_id", "size_bytes", "mime_type",
                    "created_at")
