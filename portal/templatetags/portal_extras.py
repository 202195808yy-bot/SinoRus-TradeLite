# -*- coding: utf-8 -*-
"""Дополнительные фильтры шаблонов приложения portal.

* ``tr``  — перевод произвольной русской подписи на текущий язык
            (словарь ``portal/labels.py`` + тексты ``portal/i18n.py``);
* ``fmt`` — подстановка значений в текст с заполнителями ``{n}``.

Примеры::

    {% load portal_extras %}
    {{ "Заказы"|tr }}
    {% with n=b.rows|length %}{{ ui.truncated_note|fmt:n }}{% endwith %}
"""

from django import template

from ..i18n import DEFAULT_LANG, tr as _tr

register = template.Library()


@register.filter(name="tr", takes_context=True)
def tr_filter(context, text):
    """Переводит строку на язык текущего запроса."""
    lang = context.get("LANG", DEFAULT_LANG)
    return _tr(text, lang)


@register.filter(name="fmt")
def fmt(text, value=""):
    """Подставляет значение в текст: ``"Показаны первые {n}"|fmt:5``."""
    try:
        return str(text).format(value)
    except (IndexError, KeyError, ValueError):
        return text
