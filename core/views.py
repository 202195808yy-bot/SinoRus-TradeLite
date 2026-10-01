# -*- coding: utf-8 -*-
"""平台内核的视图：通用页面渲染器与 M0 公共页面。

拆分后每个应用有自己的 ``views.py``；这里保留三样东西：

* ``_lang() / _page_data() / _page()`` —— 所有应用共用的
  渲染管线（注册表 -> 提供器 -> 模板）；
* ``set_language_view`` —— 界面语言切换端点；
* 主页、关于、帮助 —— 不属于任何业务领域的公共页。
"""

from django.shortcuts import redirect, render

from core.i18n import DEFAULT_LANG, normalize, translate_blocks
from core.pages import PAGE_BY_NAME, PAGES, app_of, title_of, purpose_of, content_of, params_of, module_name
from core.datasets import provider_for


from core.i18n import DEFAULT_LANG, normalize, translate_blocks
from core.pages import PAGE_BY_NAME, PAGES, app_of, title_of, purpose_of, content_of, params_of, module_name
from core.datasets import provider_for

def set_language_view(request, code):
    """记住所选语言并返回原始页面。

        之所以需要单独的路由，是因为 Django 管理面板会把地址中的
        ``?lang=`` 参数当作未知的列表
        过滤器并返回多余的重定向。而这里地址保持
        干净，选择则保存在会话中。
    """
    lang = normalize(code)
    if lang:
        request.session["lang"] = lang
    target = request.GET.get("next") or "/"
    # 防范开放重定向：仅允许自身的路径
    if not target.startswith("/") or target.startswith("//"):
        target = "/"
    return redirect(target)


def _lang(request):
    """当前界面语言（参见 core.middleware.LanguageMiddleware）。"""
    return getattr(request, "LANG", DEFAULT_LANG)


def _page_data(page, lang):
    """注册表条目，其名称和描述为当前语言版本。

        ``ru``/``zh``/``en`` 字段保留：模板会以提示形式显示第二种语言。
        历史键 ``purpose``/``content``（中文变体的
        同义词）会被当前语言的翻译覆盖——这样
        页面不再把俄语标题与中文正文混在一起。
    """
    data = dict(page)
    data["app"] = app_of(page)
    data["title"] = title_of(page, lang)
    data["purpose"] = purpose_of(page, lang)
    data["content"] = content_of(page, lang)
    data["params"] = params_of(page, lang)
    data["module_title"] = module_name(page["module"], lang)
    data["module_alt"] = module_name(
        page["module"], "ru" if lang == "zh" else "zh")
    return data


def _page(request, name, **extra):
    """根据注册表条目和数据提供器渲染页面。"""
    lang = _lang(request)
    page = PAGE_BY_NAME[name]
    provider = provider_for(name)
    context = {
        "page": _page_data(page, lang),
        "page_url": "/" + page["path"],
        "all_pages": PAGES,
        "prototype": provider is None,
        "blocks": [],
        "mode": None,
    }
    if provider is not None:
        data = provider(request, **extra) or {}
        context["blocks"] = translate_blocks(data.get("blocks", []), lang)
        context["mode"] = data.get("mode")
    context.update(extra)
    return render(request, "portal/page.html", context)


def set_language_view(request, code):
    """记住所选语言并返回原始页面。

        之所以需要单独的路由，是因为 Django 管理面板会把地址中的
        ``?lang=`` 参数当作未知的列表
        过滤器并返回多余的重定向。而这里地址保持
        干净，选择则保存在会话中。
    """
    lang = normalize(code)
    if lang:
        request.session["lang"] = lang
    target = request.GET.get("next") or "/"
    # 防范开放重定向：仅允许自身的路径
    if not target.startswith("/") or target.startswith("//"):
        target = "/"
    return redirect(target)


def index_view(request):
    """主页：平台概览和最新订单。"""
    lang = _lang(request)
    data = provider_for("index")(request)
    return render(request, "portal/index.html", {
        "page": _page_data(PAGE_BY_NAME["index"], lang),
        "prototype": False,
        "blocks": translate_blocks(data.get("blocks", []), lang),
        "mode": data.get("mode"),
    })


def about_view(request):
    """平台信息及其领域边界。"""
    return _page(request, "about")


def help_view(request):
    """帮助：各角色的操作说明和常见问题解答。"""
    return _page(request, "help")
