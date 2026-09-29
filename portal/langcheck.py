# -*- coding: utf-8 -*-
"""Самопроверка словаря переводов.

Проверяются две независимые вещи:

* ``scan()`` — прогоняет все провайдеры ``portal/datasets.py`` на текущих
  данных и собирает **подписи блоков**, для которых нет перевода;
* ``enum_labels()`` — собирает **перечисления** из ``choices`` моделей
  ``portal/models.py``. Они попадают в ячейки как значения (статусы, виды
  документов, единицы измерения), но по смыслу это интерфейс, поэтому
  тоже должны быть в словаре.

Вторая проверка важна: ``scan()`` видит только подписи, а перечисления
приходят значениями ячеек. Пока проверялись одни подписи, 101 подпись
``choices`` оставалась непереведённой и никто этого не замечал.

Используется тестами ``portal/tests_i18n.py`` и утилитой
``tools/check_lang.py``.
"""

import inspect
import re

from django.apps import apps
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from . import datasets as ds
from . import models as m
from .i18n import DEFAULT_LANG, LABELS, label_strings
from .pages import PAGES

#: Перечисления, которые не переводятся намеренно.
#: Условия Инкотермс — международные сокращения, одинаковые во всех языках;
#: названия языков пишутся каждое на себе; Push — имя канала уведомлений.
ENUM_SKIP = {"CIF", "CPT", "DAP", "DDP", "EXW", "FCA",
             "Русский", "中文", "Push"}


def anon_request(path="/", **params):
    """Запрос-заглушка: провайдеры читают только ``request.user`` и ``GET``."""
    request = RequestFactory().get(path, params)
    request.user = AnonymousUser()
    request.LANG = DEFAULT_LANG
    return request


def enum_labels():
    """Все подписи ``choices`` моделей приложения (кроме ``ENUM_SKIP``)."""
    out = set()
    for model in apps.get_app_config("portal").get_models():
        for field in model._meta.get_fields():
            for _value, label in (getattr(field, "choices", None) or []):
                if isinstance(label, (list, tuple)):
                    continue
                label = str(label)
                if label not in ENUM_SKIP:
                    out.add(label)
    return out


def untranslated_enums():
    """Перечисления из ``choices``, для которых нет перевода."""
    return {s for s in enum_labels() if s not in LABELS}


#: Справочники: модель -> поле с русским наименованием.
#: Небольшие закрытые перечни (страны, валюты, единицы измерения, типы
#: документов, отрасли, категории товаров). Их наименования попадают в
#: ячейки значениями, поэтому проверяются так же, как перечисления.
REFERENCE_FIELDS = (
    ("Country", "name_ru"),
    ("Currency", "name_ru"),
    ("Uom", "name_ru"),
    ("DocType", "name_ru"),
    ("Industry", "name_ru"),
    ("GoodCategory", "name_ru"),
)


def reference_values():
    """Значения справочников, которые должны быть в словаре."""
    out = set()
    for model_name, field in REFERENCE_FIELDS:
        model = getattr(m, model_name, None)
        if model is None:
            continue
        for value in model.objects.values_list(field, flat=True):
            if value:
                out.add(str(value))
    return out


def untranslated_reference_values():
    """Значения справочников, для которых нет перевода."""
    return {s for s in reference_values() if s not in LABELS}


def reference_mismatches():
    """Расхождения словаря с китайским наименованием в самом справочнике.

    У справочников есть собственное поле ``name_zh`` (см. ``seed_demo``),
    а перевод берётся из словаря. Два источника не должны расходиться,
    поэтому значения сверяются; список моделей берётся из
    ``REFERENCE_FIELDS``, но проверяются только те, у кого есть ``name_zh``.

    Возвращает список ``(модель, name_ru, в_бд, в_словаре)``.
    """
    out = []
    for model_name, field in REFERENCE_FIELDS:
        model = getattr(m, model_name, None)
        if model is None or not hasattr(model, "name_zh"):
            continue
        for name_ru, name_zh in model.objects.values_list(field, "name_zh"):
            if not name_ru or not name_zh:
                continue
            pair = LABELS.get(str(name_ru))
            if pair is None:
                continue                      # ловится untranslated_*
            if pair[0] != name_zh:
                out.append((model_name, str(name_ru), name_zh, pair[0]))
    return out


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
