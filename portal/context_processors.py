# -*- coding: utf-8 -*-
"""portal 应用的上下文处理器。"""

from django.urls import NoReverseMatch, reverse

from .i18n import (DEFAULT_LANG, LANG_HTML, LANG_LABELS, LANG_SHORT, LANGS,
                   switch_urls, ui)
from .pages import MODULES, PAGES, module_name, pages_of, title_of


def _lang(request):
    return getattr(request, "LANG", DEFAULT_LANG)


def _resolve_url(page, lang=None):
    """返回页面的实际 URL（带参数的页面为 pk=1）。"""
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
    """侧边导航结构、页面与模块名称——均为当前语言。"""
    lang = _lang(request)
    #: 名称的第二语言（双语平台两者都显示）
    alt = "ru" if lang == "zh" else "zh"

    urls = switch_urls(request)
    context = {
        "LANG": lang,
        "LANG_HTML": LANG_HTML[lang],
        "ui": ui(lang),
        "langs": [{"code": code,
                   "label": LANG_LABELS[code],
                   "short": LANG_SHORT[code],
                   "url": urls[code],
                   "active": code == lang} for code in LANGS],
    }

    # 管理面板不需要应用导航——因此不构建它，
    # 以免每个 /admin/ 请求都要访问 urlconf 43 次。
    # 那里的语言切换器通过上面的同一个上下文工作。
    if request.path.startswith("/admin/"):
        return context

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

    context["nav_modules"] = modules
    context["page_index"] = [{**p, "title": title_of(p, lang),
                              "url": _resolve_url(p, lang)} for p in PAGES]
    return context
