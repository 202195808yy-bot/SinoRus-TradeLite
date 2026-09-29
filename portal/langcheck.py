# -*- coding: utf-8 -*-
"""Самопроверка словаря переводов.

Прогоняет все провайдеры ``portal/datasets.py`` на текущих данных и
собирает подписи блоков, для которых нет перевода в ``portal/labels.py``.
Так словарь не разъезжается с кодом: если провайдер добавит новую
подпись, проверка это покажет.

Используется тестом ``portal/tests_i18n.py`` и утилитой
``tools/check_lang.py``.
"""

import inspect
import re

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from . import datasets as ds
from . import models as m
from .i18n import DEFAULT_LANG, LABELS, label_strings
from .pages import PAGES


def anon_request(path="/", **params):
    """Запрос-заглушка: провайдеры читают только ``request.user`` и ``GET``."""
    request = RequestFactory().get(path, params)
    request.user = AnonymousUser()
    request.LANG = DEFAULT_LANG
    return request


def provider_pk(fn):
    """pk первого объекта для страницы с параметром (или None)."""
    if "pk" not in inspect.signature(fn).parameters:
        return None
    match = re.search(r"get_object_or_404\(\s*(?:\w+\.)?(\w+)",
                      inspect.getsource(fn))
    if not match:
        return None
    model = getattr(m, match.group(1), None)
    if model is None:
        return None
    obj = model.objects.first()
    return obj.pk if obj is not None else None


def scan():
    """Прогоняет провайдеры и возвращает (все подписи, непереведённые).

    Провайдеры, которые не удалось выполнить (нет данных), пропускаются
    со счётчиком.
    """
    found = set()
    skipped = []
    for page in PAGES:
        name = page["name"]
        fn = ds.PAGE_DATA.get(name)
        if fn is None:
            continue
        kwargs = {}
        if "pk" in inspect.signature(fn).parameters:
            pk = provider_pk(fn)
            if pk is None:
                skipped.append(name)
                continue
            kwargs["pk"] = pk
        try:
            data = fn(anon_request(), **kwargs) or {}
        except Exception as exc:                              # noqa: BLE001
            skipped.append("%s (%s)" % (name, type(exc).__name__))
            continue
        found |= label_strings(data.get("blocks") or [])
    return found, {s for s in found if s not in LABELS}, skipped


def untranslated_in(blocks):
    """Непереведённые подписи в уже собранных блоках."""
    return {s for s in label_strings(blocks) if s not in LABELS}
