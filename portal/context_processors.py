# -*- coding: utf-8 -*-
"""Контекстные процессоры приложения portal."""

from django.urls import NoReverseMatch, reverse

from .i18n import (DEFAULT_LANG, LANG_HTML, LANG_LABELS, LANG_SHORT, LANGS,
                   switch_urls, ui)
from .pages import MODULES, PAGES, module_name, pages_of, title_of


def _lang(request):
    return getattr(request, "LANG", DEFAULT_LANG)


def _resolve_url(page, lang=None):
    """Возвращает фактический URL страницы (для страниц с параметром — pk=1)."""
    try:
        if "<int:pk>" in page["path"]:
            url = reverse("portal:" + page["name"], kwargs={"pk": 1})
        else:
            url = reverse("portal:" + page["name"])
    except NoReverseMatch:
        url = "/" + page["path"]
    if lang and lang != DEFAULT_LANG:
        url += "?lang=" + lang
    return url


def navigation(request):
    """Структура боковой навигации, названия страниц и модулей — на текущем языке."""
    lang = _lang(request)
    #: второй язык названия (для двуязычной платформы показываем оба)
    alt = "ru" if lang == "zh" else "zh"

    modules = []
    for code, ru, zh, en in MODULES:
        modules.append({
            "code": code,
            "title": module_name(code, lang),
            "alt": module_name(code, alt),
            "ru": ru,
            "zh": zh,
            "en": en,
            "pages": [{**p, "title": title_of(p, lang),
                       "url": _resolve_url(p, lang)}
                      for p in pages_of(code)],
        })

    urls = switch_urls(request)
    return {
        "nav_modules": modules,
        "page_index": [{**p, "title": title_of(p, lang),
                        "url": _resolve_url(p, lang)} for p in PAGES],
        "LANG": lang,
        "LANG_HTML": LANG_HTML[lang],
        "ui": ui(lang),
        "langs": [{"code": code,
                   "label": LANG_LABELS[code],
                   "short": LANG_SHORT[code],
                   "url": urls[code],
                   "active": code == lang} for code in LANGS],
    }
