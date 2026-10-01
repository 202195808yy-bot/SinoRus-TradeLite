# -*- coding: utf-8 -*-
"""跨应用遍历模型的助手。

拆分后模型分散在 11 个应用里，而管理面板标签翻译、
语言字典自检等工具需要「本项目全部模型」这一视图。
集中在这里，避免每处各写一遍应用清单
（清单的唯一来源是 ``settings.PROJECT_APPS``）。
"""

from django.apps import apps
from django.conf import settings


def project_app_labels():
    """本项目自己的应用标签（不含 django.contrib.*）。"""
    return tuple(getattr(settings, "PROJECT_APPS", ()))


def project_app_configs():
    """本项目应用的 ``AppConfig``，按 ``INSTALLED_APPS`` 顺序。"""
    return [apps.get_app_config(label) for label in project_app_labels()
            if label in apps.app_configs]


def project_models():
    """本项目全部实体模型（不含自动生成的 M2M 中间模型）。"""
    for config in project_app_configs():
        yield from config.get_models()


def model_by_name(name):
    """按类名取模型（跨应用）；不存在返回 None。"""
    for model in project_models():
        if model.__name__ == name:
            return model
    return None
