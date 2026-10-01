# -*- coding: utf-8 -*-
"""商品与参考字典 的页面数据提供器。

区块构造器与工具函数在 ``core/datasets.py``；
这里只放本应用页面自己的取数逻辑，并在模块末尾
用 ``PROVIDERS`` 声明页面名到提供器的映射。
"""

from decimal import Decimal

from django.shortcuts import get_object_or_404
from django.db.models import Q

from core.datasets import (c, dt, fld, k, kpi, num, q_param, safe, tbl, url_for)
from catalog.models import Good, GoodCategory, Packaging, Uom


def goods_list_data(request, **kw):
    qs = (Good.objects
          .select_related("category", "uom", "category__parent"))
    q, cat, active = q_param(request, "q"), q_param(request, "category"), q_param(request, "active")
    if q:
        qs = qs.filter(Q(name_ru__icontains=q) | Q(name_zh__icontains=q)
                       | Q(sku__icontains=q) | Q(brand__icontains=q))
    if cat:
        qs = qs.filter(Q(category__code=cat) | Q(category__parent__code=cat))
    if active in ("1", "0"):
        qs = qs.filter(is_active=(active == "1"))
    blocks = [
        kpi("Каталог", [
            k("Товаров", Good.objects.count(), "всего"),
            k("Активных", Good.objects.filter(is_active=True).count()),
            k("Категорий", GoodCategory.objects.count()),
            k("Упаковок", Packaging.objects.count(), "описано"),
        ]),
        tbl("Товары",
            ["Артикул", "Наименование", "Наименование (кит.)", "Категория",
             "Единица", "Активен"],
            [[c(g.sku, url_for("goods_detail", g.pk), mono=True),
              c(g.name_ru), c(g.name_zh or "—"),
              c(safe(g.category, "name_ru")),
              c(safe(g.uom, "code")),
              c("да" if g.is_active else "нет")]
             for g in qs],
            empty="Товары не найдены",
            note=("Отбор: поиск «%s»" % q) if q else None),
    ]
    return {"blocks": blocks}


def goods_detail_data(request, pk, **kw):
    g = get_object_or_404(
        Good.objects.select_related("category", "uom"), pk=pk)
    attrs = g.attributes or {}
    blocks = [
        fld("Карточка товара", [
            ("Артикул (SKU)", g.sku),
            ("Код ТН ВЭД", g.hs_code or "—"),
            ("Наименование (рус.)", g.name_ru),
            ("Наименование (кит.)", g.name_zh or "—"),
            ("Категория", safe(g.category, "name_ru")),
            ("Единица измерения", safe(g.uom, "name_ru")),
            ("Торговая марка", g.brand or "—"),
            ("Срок хранения, сут", g.shelf_life_days or "—"),
            ("В каталоге", "да" if g.is_active else "нет"),
            ("Создан", dt(g.created_at)),
        ]),
        fld("Характеристики", list(attrs.items()) or [("—", "не заполнены")]),
        tbl("Упаковка",
            ["Вид", "Штук в упаковке", "Вес, кг", "Габариты"],
            [[c(p.get_kind_display()), c(num(p.units_per_pack)),
              c(num(p.unit_weight_kg, 3)), c(p.dims or "—")]
             for p in g.packagings.all()],
            empty="Упаковка не описана"),
        tbl("Изображения",
            ["Файл", "Порядок", "Главное"],
            [[c(im.file.name or "—"), c(num(im.order)),
              c("да" if im.is_main else "нет")]
             for im in g.images.all()],
            empty="Изображений нет"),
        tbl("Сертификаты товара",
            ["Номер", "Вид", "Действителен до", "Осталось дней"],
            [[c(cert.number, mono=True), c(cert.get_kind_display()),
              c(dt(cert.valid_until)),
              c(cert.days_to_expiry)]
             for cert in g.certificates.all()],
            empty="Сертификаты не заведены"),
    ]
    return {"blocks": blocks}


def goods_form_data(request, **kw):
    blocks = [
        tbl("Справочник категорий",
            ["Код", "Наименование", "Уровень", "Родительская категория"],
            [[c(cat.code, mono=True), c(cat.name_ru), c(num(cat.level)),
              c(safe(cat.parent, "name_ru"))]
             for cat in GoodCategory.objects.select_related("parent")],
            empty="Категории не заведены"),
        tbl("Единицы измерения",
            ["Код", "Наименование", "Вид"],
            [[c(u.code, mono=True), c(u.name_ru), c(u.get_kind_display())]
             for u in Uom.objects.all()],
            empty="Единицы не заведены"),
    ]
    return {"blocks": blocks}


#: 本应用页面的提供器（在 ``apps.ready()`` 中登记）。
PROVIDERS = {
    "goods_detail": goods_detail_data,
    "goods_form": goods_form_data,
    "goods_list": goods_list_data,
}
