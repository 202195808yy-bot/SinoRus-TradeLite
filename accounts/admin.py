# -*- coding: utf-8 -*-
"""企业与账号 在管理后台中的注册。

拆分后每个应用只注册自己的模型；面板的站点标题、
分组与指标卡片分别在 ``core/admin.py``、
``core/admin_site.py``、``core/admin_kpi.py`` 中。
"""

from django.contrib import admin

from . import models as m


@admin.register(m.Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "language", "phone")
    list_filter = ("language",)
    search_fields = ("user__username", "phone")


@admin.register(m.Enterprise)
class EnterpriseAdmin(admin.ModelAdmin):
    list_display = ("name_ru", "country", "tin", "status", "created_at")
    list_filter = ("status", "country")
    search_fields = ("name_ru", "name_zh", "tin")


@admin.register(m.Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "enterprise", "role", "is_active", "joined_at")
    list_filter = ("role", "is_active")
    search_fields = ("user__username", "enterprise__name_ru")


@admin.register(m.Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("email", "enterprise", "role", "valid_until", "status")
    list_filter = ("status", "role")
    search_fields = ("email", "code")


@admin.register(m.Counterparty)
class CounterpartyAdmin(admin.ModelAdmin):
    list_display = ("name", "enterprise", "contact_person", "incoterm")
    search_fields = ("name", "contact_person")
