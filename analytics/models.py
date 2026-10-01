# -*- coding: utf-8 -*-
"""数据分析领域（模块 M9）。
指标定义、指标快照与合规风险评估。

本模块由 ``<app>/models.py`` 按限界上下文拆分而来；
模型的 ``Meta.db_table`` 显式钉住历史物理表名
（``portal_*``），因此数据库结构、索引名与文档中的
表名清单保持不变。
"""

from django.db import models
from django.utils import timezone
from trading.models import Order


class Metric(models.Model):
    """分析面板指标的定义。"""

    class Period(models.TextChoices):
        DAY = "day", "Сутки"
        WEEK = "week", "Неделя"
        MONTH = "month", "Месяц"

    code = models.CharField("код", max_length=32, unique=True)
    name_ru = models.CharField("название (рус.)", max_length=96)
    name_zh = models.CharField("название (кит.)", max_length=96)
    formula = models.CharField("формула расчёта", max_length=191, blank=True)
    unit = models.CharField("единица", max_length=16, blank=True)
    period = models.CharField("период", max_length=8,
                              choices=Period.choices,
                              default=Period.MONTH)

    class Meta:
        db_table = "portal_metric"
        verbose_name = "показатель"
        verbose_name_plural = "показатели"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name_ru}"


class MetricSnapshot(models.Model):
    """指标在周期内的取值（用于面板和历史记录）。"""

    metric = models.ForeignKey(Metric, verbose_name="показатель",
                               on_delete=models.CASCADE,
                               related_name="snapshots")
    period_key = models.CharField("период", max_length=16,
                                  help_text="Например: 2026-09")
    value = models.DecimalField("значение", max_digits=14,
                                decimal_places=2)
    calculated_at = models.DateField("рассчитано")

    class Meta:
        db_table = "portal_metricsnapshot"
        verbose_name = "снимок показателя"
        verbose_name_plural = "снимки показателей"
        ordering = ["-period_key"]
        constraints = [
            models.UniqueConstraint(fields=["metric", "period_key"],
                                    name="metricsnapshot_unique"),
        ]

    def __str__(self):
        return f"{self.metric.code} {self.period_key} = {self.value}"


class ComplianceRisk(models.Model):
    """发现的订单合规风险。"""

    class Level(models.TextChoices):
        LOW = "low", "Низкий"
        MEDIUM = "medium", "Средний"
        HIGH = "high", "Высокий"
        CRITICAL = "critical", "Критический"

    order = models.ForeignKey(Order, verbose_name="заказ",
                              on_delete=models.CASCADE,
                              related_name="risks")
    kind = models.CharField("вид риска", max_length=64)
    probability = models.CharField("вероятность", max_length=8,
                                   choices=Level.choices,
                                   default=Level.LOW)
    impact = models.CharField("ущерб", max_length=8, choices=Level.choices,
                              default=Level.MEDIUM)
    level = models.CharField("уровень", max_length=8,
                             choices=Level.choices, default=Level.LOW)
    advice = models.TextField("рекомендация", blank=True)
    detected_at = models.DateField("выявлен", default=timezone.now)

    class Meta:
        db_table = "portal_compliancerisk"
        verbose_name = "риск соответствия"
        verbose_name_plural = "риски соответствия"
        ordering = ["-detected_at"]

    def __str__(self):
        return f"{self.order.number}: {self.kind}"

__all__ = [
    "Metric", "MetricSnapshot", "ComplianceRisk",
]
