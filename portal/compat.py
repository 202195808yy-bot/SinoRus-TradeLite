# -*- coding: utf-8 -*-
"""Совместимость с Python 3.14: копирование контекста шаблона.

``requirements.txt`` закрепляет Django 4.2.30 — эта ветка поддерживает
Python 3.8–3.12 (3.13 появилась в Django 5.1, 3.14 — в 5.2). Но проект
запускают и на более новых версиях: виртуальное окружение ``.venv``
собрано на Python 3.14.

Тогда ломается копирование контекста шаблона. Django 4.2 делает так
(``django/template/context.py``)::

    def __copy__(self):
        duplicate = copy(super())
        duplicate.dicts = self.dicts[:]
        return duplicate

Приём опирается на то, что у объекта ``super()`` чтение атрибута
делегируется обёрнутому экземпляру, поэтому ``copy(super())`` возвращает
копию **контекста**, а не самого ``super``. В Python 3.14 это поведение
изменилось: ``copy(super())`` возвращает объект ``super``, и следующая
строка падает::

    AttributeError: 'super' object has no attribute 'dicts' and
    no __dict__ for setting new attributes

Внешне это выглядит так: главная страница панели открывается (она контекст
не копирует), а **любой переход** — на список моделей, на карточку, на
пользователя — отвечает ошибкой 500. В наборе тестов падают 40 из 120:
все, что отрисовывают шаблон с копированием контекста.

Обход включается в ``PortalConfig.ready()`` и только тогда, когда родная
реализация действительно сломана: на Python 3.12 и 3.13 он не включается,
и поведение остаётся штатным.
"""

import copy as _copy
import sys

#: Первая версия Python, где ``copy(super())`` перестал делегировать
#: ``__reduce_ex__`` обёрнутому объекту. Проверено на 3.12, 3.13 (работает)
#: и 3.14 (падает).
BROKEN_FROM = (3, 14)


def _copy_context(self):
    """Копия контекста без ``super()``.

    Повторяет исходную реализацию: новый объект того же типа, с тем же
    ``__dict__`` и отдельным списком ``dicts``. Копирование поверхностное —
    сам список новый, словари в нём те же.
    """
    duplicate = self.__class__.__new__(self.__class__)
    duplicate.__dict__.update(self.__dict__)
    duplicate.dicts = self.dicts[:]
    return duplicate


def patch_template_context():
    """Включает обход, если родная реализация сломана. True — если включил.

    Проверка настоящая, а не по номеру версии: копируется пустой контекст.
    Если он скопировался — вмешиваться не нужно, даже если версия Python
    формально новая.
    """
    from django.template.context import BaseContext

    if sys.version_info < BROKEN_FROM:
        return False
    if getattr(BaseContext.__copy__, "_portal_compat", False):
        return False                      # уже включён
    try:
        _copy.copy(BaseContext())
    except Exception:                     # noqa: BLE001 — именно это и проверяем
        pass
    else:
        return False                      # родная реализация работает
    _copy_context._portal_compat = True
    BaseContext.__copy__ = _copy_context
    return True
