# -*- coding: utf-8 -*-
"""物流与口岸 在管理后台中的注册。

拆分后每个应用只注册自己的模型；面板的站点标题、
分组与指标卡片分别在 ``core/admin.py``、
``core/admin_site.py``、``core/admin_kpi.py`` 中。
"""

from django.contrib import admin

from . import models as m
from core.admin_i18n import LazyRu


@admin.register(m.Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = ("pk", "display",)
    search_fields = ("pk",)

    def display(self, obj):
        return str(obj)
    display.short_description = LazyRu("значение")


@admin.register(m.BorderCrossing)
class BorderCrossingAdmin(admin.ModelAdmin):
    list_display = ("code", "name_ru", "mode", "country", "dwell_days")
    list_filter = ("mode", "country")
    search_fields = ("code", "name_ru", "name_zh")


@admin.register(m.TransportLane)
class TransportLaneAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "origin", "destination", "mode", "days")
    list_filter = ("mode",)
    search_fields = ("code", "name")


@admin.register(m.Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("number", "order", "qty", "ship_date", "container_no")
    search_fields = ("number", "container_no")


@admin.register(m.Transport)
class TransportAdmin(admin.ModelAdmin):
    list_display = ("shipment", "carrier", "mode", "lane", "waybill_no",
                    "cost")
    list_filter = ("mode",)
    search_fields = ("waybill_no",)


@admin.register(m.TrackPoint)
class TrackPointAdmin(admin.ModelAdmin):
    list_display = ("transport", "event_time", "place", "status")


@admin.register(m.Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ("number", "shipment", "kind", "severity", "status")
    list_filter = ("kind", "severity", "status")
    search_fields = ("number", "description")
