# -*- coding: utf-8 -*-
"""portal 应用的附加模板过滤器。

* ``tr``  — 将任意俄语标签译为当前语言
            (字典 ``portal/labels.py`` + ``portal/i18n.py`` 文本)；
* ``fmt`` — 将值代入含占位符 ``{n}`` 的文本。

示例::

    {% load portal_extras %}
    {{ "Заказы"|tr }}
    {% with n=b.rows|length %}{{ ui.truncated_note|fmt:n }}{% endwith %}
"""

from django import template

from ..i18n import DEFAULT_LANG, tr as _tr

register = template.Library()


@register.filter(name="tr", takes_context=True)
def tr_filter(context, text):
    """将字符串翻译为当前请求的语言。"""
    lang = context.get("LANG", DEFAULT_LANG)
    return _tr(text, lang)


@register.filter(name="fmt")
def fmt(text, value=""):
    """将值代入文本：``"Показаны первые {n}"|fmt:5``。"""
    try:
        return str(text).format(value)
    except (IndexError, KeyError, ValueError):
        return text
