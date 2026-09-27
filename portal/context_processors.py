# -*- coding: utf-8 -*-
"""Контекстные процессоры приложения portal."""

from django.urls import NoReverseMatch, reverse

from .pages import MODULES, PAGES, pages_of


def _resolve_url(page):
    """Возвращает фактический URL страницы (для страниц с параметром — pk=1)."""
    try:
        if "<int:pk>" in page["path"]:
            return reverse("portal:" + page["name"], kwargs={"pk": 1})
        return reverse("portal:" + page["name"])
    except NoReverseMatch:
        return "/" + page["path"]


def navigation(request):
    """Формирует структуру боковой навигации по модулям M0..M11."""
    modules = []
    for code, ru, zh in MODULES:
        modules.append({
            "code": code,
            "ru": ru,
            "zh": zh,
            "pages": [{**p, "url": _resolve_url(p)} for p in pages_of(code)],
        })
    return {
        "nav_modules": modules,
        "page_index": [{**p, "url": _resolve_url(p)} for p in PAGES],
    }
