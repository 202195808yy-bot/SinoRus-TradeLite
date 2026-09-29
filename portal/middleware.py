# -*- coding: utf-8 -*-
"""Middleware выбора языка интерфейса.

Язык определяется в порядке приоритета:

1. параметр запроса ``?lang=`` — и сразу запоминается в сессии;
2. значение, сохранённое в сессии предыдущим переходом;
3. ``i18n.DEFAULT_LANG``.

Результат доступен представлениям и шаблонам как ``request.LANG``.

Middleware ставится сразу после ``SessionMiddleware`` — иначе обращение
к ``request.session`` приведёт к ошибке.
"""

from .i18n import DEFAULT_LANG, normalize


class LanguageMiddleware:
    """Определяет язык интерфейса и запоминает выбор пользователя."""

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
        return self.get_response(request)
