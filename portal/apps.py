# -*- coding: utf-8 -*-
"""Конфигурация приложения portal."""

from django.apps import AppConfig


class PortalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "portal"
    verbose_name = "Портал трансграничной торговли"

    def ready(self):
        """Включает перевод подписей административной панели.

        Подписи приложения, моделей и полей берутся панелью из метаданных
        ORM и заданы по-русски. Здесь они оборачиваются в ленивый перевод
        (``portal/admin_i18n.py``), поэтому панель переключается вместе с
        остальным интерфейсом. Импорт внутри метода — на момент загрузки
        ``apps.py`` реестр приложений ещё не готов.
        """
        from .admin_i18n import localize

        localize()
