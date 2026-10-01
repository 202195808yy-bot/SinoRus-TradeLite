# -*- coding: utf-8 -*-
"""询价、报价与订单 在管理后台中的注册。

拆分后每个应用只注册自己的模型；面板的站点标题、
分组与指标卡片分别在 ``core/admin.py``、
``core/admin_site.py``、``core/admin_kpi.py`` 中。
"""

from django.contrib import admin

from . import models as m


class RfqLineInline(admin.TabularInline):
    model = m.RfqLine
    extra = 0


@admin.register(m.Rfq)
class RfqAdmin(admin.ModelAdmin):
    list_display = ("number", "title", "buyer", "due_date", "status")
    list_filter = ("status", "incoterm")
    search_fields = ("number", "title")
    inlines = [RfqLineInline]


class QuoteLineInline(admin.TabularInline):
    model = m.QuoteLine
    extra = 0


@admin.register(m.Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ("number", "rfq", "supplier", "amount", "valid_until",
                    "status")
    list_filter = ("status",)
    search_fields = ("number",)
    inlines = [QuoteLineInline]


@admin.register(m.QuoteVersion)
class QuoteVersionAdmin(admin.ModelAdmin):
    list_display = ("quote", "version", "changed_fields", "author",
                    "created_at")


class OrderLineInline(admin.TabularInline):
    model = m.OrderLine
    extra = 0


@admin.register(m.Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "buyer", "supplier", "amount", "status",
                    "signed_date")
    list_filter = ("status", "incoterm")
    search_fields = ("number",)
    inlines = [OrderLineInline]


@admin.register(m.OrderMilestone)
class OrderMilestoneAdmin(admin.ModelAdmin):
    list_display = ("order", "kind", "planned_date", "actual_date",
                    "status")
    list_filter = ("kind", "status")


@admin.register(m.OrderChange)
class OrderChangeAdmin(admin.ModelAdmin):
    list_display = ("order", "change_type", "initiated_by", "approved_by",
                    "created_at")
    list_filter = ("change_type",)
