# -*- coding: utf-8 -*-
"""结算与对账 在管理后台中的注册。

拆分后每个应用只注册自己的模型；面板的站点标题、
分组与指标卡片分别在 ``core/admin.py``、
``core/admin_site.py``、``core/admin_kpi.py`` 中。
"""

from django.contrib import admin

from . import models as m


class StatementLineInline(admin.TabularInline):
    model = m.StatementLine
    extra = 0


@admin.register(m.Statement)
class StatementAdmin(admin.ModelAdmin):
    list_display = ("number", "order", "amount", "due_date", "status")
    list_filter = ("status",)
    inlines = [StatementLineInline]


@admin.register(m.Reconciliation)
class ReconciliationAdmin(admin.ModelAdmin):
    list_display = ("order", "partner", "period", "our_amount",
                    "partner_amount", "diff", "status")
    list_filter = ("status",)


@admin.register(m.Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("statement", "paid_date", "amount", "buyer_confirmed",
                    "supplier_confirmed")
