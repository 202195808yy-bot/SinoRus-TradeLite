# -*- coding: utf-8 -*-
"""单证与合规 在管理后台中的注册。

拆分后每个应用只注册自己的模型；面板的站点标题、
分组与指标卡片分别在 ``core/admin.py``、
``core/admin_site.py``、``core/admin_kpi.py`` 中。
"""

from django.contrib import admin

from . import models as m


@admin.register(m.DocType)
class DocTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "name_ru", "stage")
    list_filter = ("stage",)


@admin.register(m.Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("doc_type", "order", "issuer", "issued_date",
                    "valid_until", "status")
    list_filter = ("status", "doc_type")
    date_hierarchy = "issued_date"


@admin.register(m.Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("number", "kind", "good", "valid_until", "fgis_no")
    list_filter = ("kind",)
    search_fields = ("number", "fgis_no")


@admin.register(m.DocRequirement)
class DocRequirementAdmin(admin.ModelAdmin):
    list_display = ("order", "doc_type", "status")
    list_filter = ("status",)


@admin.register(m.ComplianceCheck)
class ComplianceCheckAdmin(admin.ModelAdmin):
    list_display = ("order", "result", "checker", "checked_at")
    list_filter = ("result",)


@admin.register(m.DeadlineReminder)
class DeadlineReminderAdmin(admin.ModelAdmin):
    list_display = ("target_kind", "target_id", "due_date", "recipient",
                    "status")
    list_filter = ("status", "target_kind")
