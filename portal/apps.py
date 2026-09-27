# -*- coding: utf-8 -*-
"""Конфигурация приложения portal."""

from django.apps import AppConfig


class PortalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "portal"
    verbose_name = "Портал трансграничной торговли"
