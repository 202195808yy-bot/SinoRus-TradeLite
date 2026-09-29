# -*- coding: utf-8 -*-
"""Middleware выбора языка интерфейса.

Язык определяется в порядке приоритета:

1. параметр запроса ``?lang=`` — и сразу запоминается в сессии;
2. значение, сохранённое в сессии предыдущим переходом;
3. ``i18n.DEFAULT_LANG``.

Результат доступен представлениям и шаблонам как ``request.LANG``.

Дополнительно активируется локаль Django (``translation.override``).
Благодаря этому административная панель — её переводы входят в поставку
Django — переключается тем же выбором языка, хотя собственных шаблонов
у неё нет. Локаль действует только на время запроса: после ответа
восстанавливается прежняя, поэтому выбор языка не «протекает» дальше.

Порядок в ``MIDDLEWARE``: **после** ``SessionMiddleware`` (нужен доступ
к ``request.session``) и **после** ``LocaleMiddleware`` — иначе тот
перезапишет активированную локаль, выбрав её по cookie и заголовку
``Accept-Language``.
"""

from django.utils import translation

from .i18n import DEFAULT_LANG, LANG_DJANGO, normalize


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

        code = LANG_DJANGO[lang]
        request.LANGUAGE_CODE = code
        # Именно override, а не activate: локаль восстанавливается после
        # ответа, поэтому выбор языка не «протекает» в следующий запрос,
        # выполненный в том же потоке (существенно для тестов, где запросы
        # идут подряд, и для ленивых подписей админ-панели, которые читают
        # активную локаль в момент вывода).
        with translation.override(code):
            return self.get_response(request)
