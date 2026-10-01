# -*- coding: utf-8 -*-
"""平台共享内核：抽象基类 ``TimeStampedModel`` / ``DocNumberMixin``、
跨领域的值字典 ``Incoterm`` 与 ``TransportMode``。
不定义实体表——本应用是其他应用的公共依赖。

本模块由 ``<app>/models.py`` 按限界上下文拆分而来；
模型的 ``Meta.db_table`` 显式钉住历史物理表名
（``portal_*``），因此数据库结构、索引名与文档中的
表名清单保持不变。
"""

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """带记录创建与修改时间戳的抽象模型。"""

    created_at = models.DateTimeField("создано", auto_now_add=True)
    updated_at = models.DateTimeField("обновлено", auto_now=True)

    class Meta:
        abstract = True


class DocNumberMixin:
    """首次保存时生成 ``前缀-年份-序号`` 形式的编号。"""

    number_prefix = "DOC"

    def generate_number(self):
        year = timezone.now().year
        seq = type(self).objects.count() + 1
        return f"{self.number_prefix}-{year:04d}-{seq:04d}"

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self.generate_number()
        super().save(*args, **kwargs)


class Incoterm(models.TextChoices):
    EXW = "EXW", "EXW"
    FCA = "FCA", "FCA"
    CPT = "CPT", "CPT"
    CIF = "CIF", "CIF"
    DAP = "DAP", "DAP"
    DDP = "DDP", "DDP"


class TransportMode(models.TextChoices):
    ROAD = "road", "Автомобильный"
    RAIL = "rail", "Железнодорожный"
    SEA = "sea", "Морской"
    AIR = "air", "Воздушный"

__all__ = [
    "TimeStampedModel", "DocNumberMixin", "Incoterm",
    "TransportMode",
]
