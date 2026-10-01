# -*- coding: utf-8 -*-
"""数据看板 在管理后台中的注册。

拆分后每个应用只注册自己的模型；面板的站点标题、
分组与指标卡片分别在 ``core/admin.py``、
``core/admin_site.py``、``core/admin_kpi.py`` 中。
"""

from django.contrib import admin

from . import models as m


@admin.register(m.Metric)
class MetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name_ru", "unit", "period")


@admin.register(m.MetricSnapshot)
class MetricSnapshotAdmin(admin.ModelAdmin):
    list_display = ("metric", "period_key", "value", "calculated_at")


@admin.register(m.ComplianceRisk)
class ComplianceRiskAdmin(admin.ModelAdmin):
    list_display = ("order", "kind", "probability", "impact", "level")
    list_filter = ("level",)
