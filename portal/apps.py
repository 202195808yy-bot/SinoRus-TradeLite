# -*- coding: utf-8 -*-
"""Конфигурация приложения portal."""

from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig

#: Класс сайта панели. ``django.contrib.admin.sites.site`` — ленивый
#: объект: он читает ``default_site`` у конфигурации приложения admin
#: при ПЕРВОМ обращении, а первое обращение происходит в
#: ``AdminConfig.ready()`` -> ``autodiscover()``. Значит значение должно
#: быть задано до ``django.setup()`` — то есть на уровне модуля, а не в
#: ``ready()``: к тому моменту реестр уже наполнен моделями.
AdminConfig.default_site = "portal.admin_site.TradeHubAdminSite"


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

        Здесь же включается обход для Python 3.14: Django 4.2 копирует
        контекст шаблона через ``copy(super())``, а там это больше не
        работает — падают все страницы панели, кроме главной
        (``portal/compat.py``).
        """
        from .admin_i18n import localize
        from .compat import patch_template_context

        patch_template_context()
        localize()
