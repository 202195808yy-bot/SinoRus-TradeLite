# -*- coding: utf-8 -*-
"""界面语言选择的中间件。

语言按优先级顺序确定：

1. 请求参数 ``?lang=``——并立即存入会话；
2. 上一次跳转时保存在会话中的值；
3. ``i18n.DEFAULT_LANG``。

结果以 ``request.LANG`` 的形式供视图和模板使用。

此外还会激活 Django 语言环境（``translation.override``）。
因此管理面板——其译文随 Django 一同发布——
虽然没有自己的模板，也能通过同一语言选择进行切换。
语言环境只在请求期间生效：响应之后
恢复原来的设置，因此语言选择不会继续“泄漏”。

在 ``MIDDLEWARE`` 中的顺序：位于 ``SessionMiddleware`` **之后**（需要
访问 ``request.session``），并且位于 ``LocaleMiddleware`` **之后**——
否则后者会根据 cookie 和
``Accept-Language`` 请求头选择语言环境，覆盖已激活的语言环境。
"""

from django.utils import translation

from .i18n import DEFAULT_LANG, LANG_DJANGO, normalize


class LanguageMiddleware:
    """确定界面语言并记住用户的选择。"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        requested = normalize(request.GET.get("lang"))
        if requested:
            request.session["lang"] = requested
            lang = requested
        else:
            lang = normalize(request.session.get("lang")) or DEFAULT_LANG
        request.LANG = lang

        code = LANG_DJANGO[lang]
        request.LANGUAGE_CODE = code
        # 用的是 override 而非 activate：语言环境会在响应之后
        # 恢复，因此语言选择不会“泄漏”到在同一线程中执行的
        # 下一个请求（这对测试至关重要——测试中的请求
        # 连续执行；对在输出时读取当前语言环境的
        # 管理面板延迟标签而言也是如此）。
        with translation.override(code):
            return self.get_response(request)
