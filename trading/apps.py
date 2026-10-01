# -*- coding: utf-8 -*-
"""询价、报价与订单 的应用配置。"""

from django.apps import AppConfig


class TradingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "trading"
    verbose_name = "Запросы, предложения и заказы"

    def ready(self):
        """登记本应用的页面数据提供器。

        提供器在 ``trading/datasets.py`` 里以 ``PROVIDERS`` 声明；
        集中登记到 ``core.datasets.PAGE_DATA``，视图侧只需按
        页面名查找，不必知道页面属于哪个应用。
        """
        from core.datasets import register_providers

        from . import datasets

        register_providers(datasets.PROVIDERS)
