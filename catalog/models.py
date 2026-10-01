# -*- coding: utf-8 -*-
"""商品与通用参考字典领域（模块 M2）。
币种、国家、计量单位、行业、商品类别，以及商品本身、
包装与图片。

本模块由 ``<app>/models.py`` 按限界上下文拆分而来；
模型的 ``Meta.db_table`` 显式钉住历史物理表名
（``portal_*``），因此数据库结构、索引名与文档中的
表名清单保持不变。
"""

from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from core.models import TimeStampedModel


class Currency(models.Model):
    """货币字典。"""

    code = models.CharField("код", max_length=3, unique=True,
                            validators=[RegexValidator(r"^[A-Z]{3}$")])
    name_ru = models.CharField("название (рус.)", max_length=64)
    name_zh = models.CharField("название (кит.)", max_length=64)
    symbol = models.CharField("символ", max_length=4)
    decimals = models.PositiveSmallIntegerField("знаков после запятой",
                                                default=2)

    class Meta:
        db_table = "portal_currency"
        verbose_name = "валюта"
        verbose_name_plural = "валюты"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} ({self.symbol})"


class Country(models.Model):
    """贸易参与国字典。"""

    code2 = models.CharField("код ISO 3166-1 alpha-2", max_length=2,
                             unique=True)
    name_ru = models.CharField("название (рус.)", max_length=64)
    name_zh = models.CharField("название (кит.)", max_length=64)
    currency = models.ForeignKey(Currency, verbose_name="основная валюта",
                                 on_delete=models.PROTECT, null=True,
                                 blank=True, related_name="countries")
    timezone = models.CharField("часовой пояс", max_length=32,
                                default="Asia/Shanghai")

    class Meta:
        db_table = "portal_country"
        verbose_name = "страна"
        verbose_name_plural = "страны"
        ordering = ["code2"]

    def __str__(self):
        return f"{self.code2} — {self.name_ru}"


class Uom(models.Model):
    """商品计量单位。"""

    class Kind(models.TextChoices):
        COUNT = "count", "Штуки"
        WEIGHT = "weight", "Масса"
        VOLUME = "volume", "Объём"

    code = models.CharField("код", max_length=8, unique=True)
    name_ru = models.CharField("название (рус.)", max_length=32)
    name_zh = models.CharField("название (кит.)", max_length=32)
    kind = models.CharField("тип", max_length=8, choices=Kind.choices,
                            default=Kind.COUNT)

    class Meta:
        db_table = "portal_uom"
        verbose_name = "единица измерения"
        verbose_name_plural = "единицы измерения"
        ordering = ["code"]

    def __str__(self):
        return f"{self.name_ru} ({self.code})"


class GoodCategory(models.Model):
    """商品类别的层级字典。"""

    code = models.CharField("код", max_length=16, unique=True)
    parent = models.ForeignKey("self", verbose_name="родительская категория",
                               on_delete=models.PROTECT, null=True,
                               blank=True, related_name="children")
    name_ru = models.CharField("название (рус.)", max_length=96)
    name_zh = models.CharField("название (кит.)", max_length=96)
    level = models.PositiveSmallIntegerField("уровень вложенности", default=1)

    class Meta:
        db_table = "portal_goodcategory"
        verbose_name = "категория товара"
        verbose_name_plural = "категории товаров"
        ordering = ["code"]
        constraints = [
            models.CheckConstraint(
                check=Q(level__gte=1, level__lte=3),
                name="goodcategory_level_1_3"),
        ]

    def __str__(self):
        return f"{self.code} — {self.name_ru}"


class Industry(models.Model):
    """工业行业字典。"""

    code = models.CharField("код", max_length=16, unique=True)
    name_ru = models.CharField("название (рус.)", max_length=96)
    name_zh = models.CharField("название (кит.)", max_length=96)

    class Meta:
        db_table = "portal_industry"
        verbose_name = "отрасль"
        verbose_name_plural = "отрасли"
        ordering = ["code"]

    def __str__(self):
        return self.name_ru


class Good(TimeStampedModel):
    """商品卡片。

    阶段 1 实体“商品特性”以 JSON 字段
    ``attributes`` 实现；包装由独立模型 :class:`Packaging` 实现。
    """

    sku = models.CharField("артикул (SKU)", max_length=32, unique=True,
                           validators=[RegexValidator(
                               r"^[A-Z0-9][A-Z0-9-]{2,31}$",
                               "Артикул: заглавные буквы, цифры и дефис")])
    hs_code = models.CharField("код ТН ВЭД", max_length=12, blank=True,
                               validators=[RegexValidator(
                                   r"^\d{4,12}$", "Только цифры")])
    name_ru = models.CharField("название (рус.)", max_length=191)
    name_zh = models.CharField("название (кит.)", max_length=191)
    category = models.ForeignKey(GoodCategory,
                                 verbose_name="категория",
                                 on_delete=models.PROTECT,
                                 related_name="goods")
    uom = models.ForeignKey(Uom, verbose_name="единица измерения",
                            on_delete=models.PROTECT,
                            related_name="goods")
    brand = models.CharField("торговая марка", max_length=64, blank=True)
    shelf_life_days = models.PositiveIntegerField(
        "срок хранения, сут", null=True, blank=True)
    attributes = models.JSONField(
        "характеристики", default=dict, blank=True,
        help_text="Например: {\"Мощность\": \"150 Вт\"}")
    description_ru = models.TextField("описание (рус.)", blank=True)
    description_zh = models.TextField("описание (кит.)", blank=True)
    is_active = models.BooleanField("в каталоге", default=True)

    class Meta:
        db_table = "portal_good"
        verbose_name = "товар"
        verbose_name_plural = "товары"
        ordering = ["sku"]
        indexes = [models.Index(fields=["category", "is_active"])]

    def __str__(self):
        return f"{self.sku} — {self.name_ru}"


class Packaging(models.Model):
    """商品包装规格。"""

    class Kind(models.TextChoices):
        BOX = "box", "Коробка"
        PALLET = "pallet", "Паллет"
        BAG = "bag", "Мешок"
        CONTAINER = "container", "Контейнер"

    good = models.ForeignKey(Good, verbose_name="товар",
                             on_delete=models.CASCADE,
                             related_name="packagings")
    kind = models.CharField("тип упаковки", max_length=16,
                            choices=Kind.choices, default=Kind.BOX)
    units_per_pack = models.PositiveIntegerField("штук в упаковке",
                                                 default=1)
    unit_weight_kg = models.DecimalField(
        "масса места, кг", max_digits=10, decimal_places=3,
        null=True, blank=True)
    dims = models.CharField("габариты (ДхШхВ), см", max_length=32,
                            blank=True)

    class Meta:
        db_table = "portal_packaging"
        verbose_name = "упаковка"
        verbose_name_plural = "упаковки"
        ordering = ["good", "kind"]
        constraints = [
            models.CheckConstraint(
                check=Q(units_per_pack__gte=1),
                name="packaging_units_positive"),
        ]

    def __str__(self):
        return f"{self.good.sku}: {self.get_kind_display()}"


class ProductImage(models.Model):
    """商品卡片中的图片。"""

    good = models.ForeignKey(Good, verbose_name="товар",
                             on_delete=models.CASCADE,
                             related_name="images")
    file = models.FileField("файл", upload_to="goods/%Y/%m")
    order = models.PositiveSmallIntegerField("порядок", default=0)
    is_main = models.BooleanField("главное изображение", default=False)

    class Meta:
        db_table = "portal_productimage"
        verbose_name = "изображение товара"
        verbose_name_plural = "изображения товаров"
        ordering = ["good", "order"]
        constraints = [
            models.UniqueConstraint(
                fields=["good"], condition=Q(is_main=True),
                name="productimage_single_main"),
        ]

    def __str__(self):
        return f"{self.good.sku} #{self.order}"

__all__ = [
    "Currency", "Country", "Uom",
    "GoodCategory", "Industry", "Good",
    "Packaging", "ProductImage",
]
