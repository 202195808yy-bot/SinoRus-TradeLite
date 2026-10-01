# -*- coding: utf-8 -*-
"""商品与参考字典 在管理后台中的注册。

拆分后每个应用只注册自己的模型；面板的站点标题、
分组与指标卡片分别在 ``core/admin.py``、
``core/admin_site.py``、``core/admin_kpi.py`` 中。
"""

from django.contrib import admin

from . import models as m
from core.admin_i18n import LazyRu


@admin.register(m.Country, m.Currency, m.GoodCategory, m.Industry, m.Uom)
class MasterDataAdmin(admin.ModelAdmin):
    list_display = ("pk", "display",)
    search_fields = ("pk",)

    def display(self, obj):
        return str(obj)
    display.short_description = LazyRu("значение")


class PackagingInline(admin.TabularInline):
    model = m.Packaging
    extra = 0


class ProductImageInline(admin.TabularInline):
    model = m.ProductImage
    extra = 0


@admin.register(m.Good)
class GoodAdmin(admin.ModelAdmin):
    list_display = ("sku", "name_ru", "category", "uom", "brand",
                    "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("sku", "name_ru", "name_zh", "hs_code")
    inlines = [PackagingInline, ProductImageInline]


@admin.register(m.Packaging)
class PackagingAdmin(admin.ModelAdmin):
    list_display = ("good", "kind", "units_per_pack", "unit_weight_kg")
    list_filter = ("kind",)


@admin.register(m.ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("good", "order", "is_main")
