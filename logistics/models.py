# -*- coding: utf-8 -*-
"""物流与口岸领域（模块 M5）。
口岸、运输通道、费率，以及批次、运输、轨迹点与在途异常事件。

本模块由 ``<app>/models.py`` 按限界上下文拆分而来；
模型的 ``Meta.db_table`` 显式钉住历史物理表名
（``portal_*``），因此数据库结构、索引名与文档中的
表名清单保持不变。
"""

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from core.i18n import label
from core.models import DocNumberMixin, TimeStampedModel, TransportMode
from accounts.models import Enterprise
from catalog.models import Country
from trading.models import Order


class BorderCrossing(models.Model):
    """海关通关口岸。"""

    code = models.CharField("код", max_length=16, unique=True)
    name_ru = models.CharField("название (рус.)", max_length=96)
    name_zh = models.CharField("название (кит.)", max_length=96)
    mode = models.CharField("вид транспорта", max_length=8,
                            choices=TransportMode.choices,
                            default=TransportMode.ROAD)
    country = models.ForeignKey(Country, verbose_name="страна",
                                on_delete=models.PROTECT,
                                related_name="crossings")
    capacity_t_per_day = models.DecimalField(
        "пропускная способность, т/сут", max_digits=9, decimal_places=1,
        null=True, blank=True)
    dwell_days = models.DecimalField(
        "среднее время пребывания, сут", max_digits=4, decimal_places=1,
        null=True, blank=True)

    class Meta:
        db_table = "portal_bordercrossing"
        verbose_name = "пункт пропуска"
        verbose_name_plural = "пункты пропуска"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name_ru}"


class TransportLane(models.Model):
    """两个口岸之间的物流通道。"""

    code = models.CharField("код", max_length=16, unique=True)
    name = models.CharField("название", max_length=128)
    origin = models.ForeignKey(BorderCrossing,
                               verbose_name="пункт отправления",
                               on_delete=models.PROTECT,
                               related_name="lanes_from")
    destination = models.ForeignKey(
        BorderCrossing, verbose_name="пункт назначения",
        on_delete=models.PROTECT, related_name="lanes_to")
    mode = models.CharField("вид транспорта", max_length=8,
                            choices=TransportMode.choices,
                            default=TransportMode.ROAD)
    days = models.DecimalField("сроки доставки, сут", max_digits=5,
                               decimal_places=1)
    price_per_kg = models.DecimalField(
        "стоимость, за кг", max_digits=9, decimal_places=2,
        null=True, blank=True)

    class Meta:
        db_table = "portal_transportlane"
        verbose_name = "логистический канал"
        verbose_name_plural = "логистические каналы"
        ordering = ["code"]
        constraints = [
            models.CheckConstraint(
                check=~Q(origin=models.F("destination")),
                name="lane_origin_differs_destination"),
        ]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Tariff(models.Model):
    """按 ТН ВЭД（海关商品编码）编码的海关关税。"""

    hs_code = models.CharField("код ТН ВЭД", max_length=12, unique=True,
                               validators=[RegexValidator(r"^\d{4,12}$")])
    duty_rate = models.DecimalField(
        "пошлина, %", max_digits=5, decimal_places=2)
    vat_rate = models.DecimalField(
        "НДС, %", max_digits=5, decimal_places=2)
    valid_from = models.DateField("действует с")

    class Meta:
        db_table = "portal_tariff"
        verbose_name = "таможенный тариф"
        verbose_name_plural = "таможенные тарифы"
        ordering = ["hs_code"]

    def __str__(self):
        return (f"{self.hs_code}: {label('пошлина')} {self.duty_rate}%,"
                f" {label('НДС')} {self.vat_rate}%")


class Shipment(DocNumberMixin, TimeStampedModel):
    """订单范围内的批次（发货）。"""

    number_prefix = "SHP"

    number = models.CharField("номер", max_length=24, unique=True,
                              blank=True)
    order = models.ForeignKey(Order, verbose_name="заказ",
                              on_delete=models.PROTECT,
                              related_name="shipments")
    qty = models.DecimalField("количество", max_digits=12,
                              decimal_places=3)
    weight_kg = models.DecimalField("масса, кг", max_digits=12,
                                    decimal_places=2, null=True, blank=True)
    volume_m3 = models.DecimalField(
        "объём, м³", max_digits=12, decimal_places=3, null=True, blank=True)
    ship_date = models.DateField("дата отгрузки", null=True, blank=True)
    container_no = models.CharField(
        "номер контейнера", max_length=16, blank=True)

    class Meta:
        db_table = "portal_shipment"
        verbose_name = "партия"
        verbose_name_plural = "партии"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.number} ({self.order.number})"


class Transport(models.Model):
    """批次运输：承运方、渠道、单证。"""

    shipment = models.OneToOneField(
        Shipment, verbose_name="партия", on_delete=models.CASCADE,
        related_name="transport")
    carrier = models.ForeignKey(
        Enterprise, verbose_name="перевозчик", on_delete=models.PROTECT,
        null=True, blank=True, related_name="transports")
    carrier_name = models.CharField(
        "название перевозчика", max_length=128, blank=True,
        help_text="Заполняется, если перевозчик не зарегистрирован")
    mode = models.CharField("вид транспорта", max_length=8,
                            choices=TransportMode.choices,
                            default=TransportMode.ROAD)
    lane = models.ForeignKey(TransportLane, verbose_name="канал",
                             on_delete=models.PROTECT, null=True, blank=True,
                             related_name="transports")
    waybill_no = models.CharField("транспортная накладная", max_length=32,
                                  blank=True)
    cost = models.DecimalField("стоимость перевозки", max_digits=12,
                               decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "portal_transport"
        verbose_name = "перевозка"
        verbose_name_plural = "перевозки"

    def __str__(self):
        who = self.carrier or self.carrier_name or "—"
        return f"{self.shipment.number}: {who}"


class TrackPoint(models.Model):
    """运输路线节点（跟踪要素）。"""

    transport = models.ForeignKey(Transport, verbose_name="перевозка",
                                  on_delete=models.CASCADE,
                                  related_name="track_points")
    event_time = models.DateTimeField("время события")
    place = models.CharField("место", max_length=128)
    status = models.CharField("статус", max_length=64)
    note = models.CharField("примечание", max_length=191, blank=True)

    class Meta:
        db_table = "portal_trackpoint"
        verbose_name = "точка маршрута"
        verbose_name_plural = "точки маршрута"
        ordering = ["transport", "event_time"]

    def __str__(self):
        return f"{self.place}: {self.status}"


class Incident(DocNumberMixin, TimeStampedModel):
    """批次的负面偏差（异常事件）。"""

    number_prefix = "INC"

    class Kind(models.TextChoices):
        DELAY = "delay", "Просрочка"
        DAMAGE = "damage", "Повреждение"
        SHORTAGE = "shortage", "Недовоз"
        CUSTOMS = "customs", "Таможня"
        OTHER = "other", "Прочее"

    class Severity(models.TextChoices):
        LOW = "low", "Низкая"
        MEDIUM = "medium", "Средняя"
        HIGH = "high", "Высокая"
        CRITICAL = "critical", "Критическая"

    class Status(models.TextChoices):
        REGISTERED = "registered", "Зарегистрирован"
        IN_PROGRESS = "in_progress", "В работе"
        RESOLVED = "resolved", "Урегулирован"
        CLOSED = "closed", "Закрыт"

    number = models.CharField("номер", max_length=24, unique=True,
                              blank=True)
    shipment = models.ForeignKey(Shipment, verbose_name="партия",
                                 on_delete=models.PROTECT,
                                 related_name="incidents")
    kind = models.CharField("тип", max_length=16, choices=Kind.choices)
    severity = models.CharField("критичность", max_length=8,
                                choices=Severity.choices,
                                default=Severity.MEDIUM)
    description = models.TextField("описание")
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="заявитель",
        on_delete=models.SET_NULL, null=True, related_name="incidents")
    status = models.CharField("статус", max_length=16,
                              choices=Status.choices,
                              default=Status.REGISTERED)
    resolution = models.TextField("результат", blank=True)

    class Meta:
        db_table = "portal_incident"
        verbose_name = "инцидент"
        verbose_name_plural = "инциденты"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "severity"])]

    def __str__(self):
        return f"{self.number}: {self.get_kind_display()}"

__all__ = [
    "BorderCrossing", "TransportLane", "Tariff",
    "Shipment", "Transport", "TrackPoint",
    "Incident",
]
