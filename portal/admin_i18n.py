# -*- coding: utf-8 -*-
"""Ленивый перевод подписей административной панели.

Django строит подписи панели из метаданных моделей: ``verbose_name``
приложения (``portal/apps.py``), моделей и полей (``portal/models.py``),
подписи ``choices`` (статусы, виды документов, единицы измерения), а также
``site_header`` / ``index_title`` (``portal/admin.py``). Все они заданы
по-русски и от языка интерфейса не зависят — поэтому при выбранном китайском
оболочка панели переводилась (её переводы входят в поставку Django),
а названия моделей, полей и значений оставались русскими.

Решение — обернуть подписи в ленивую обёртку, которая переводится **в момент
вывода**, когда активна выбранная локаль. Обёрток две, потому что требования
к ним разные.

``LazyRu`` — обёртка-``Promise`` для подписей (``verbose_name``,
``help_text``, заголовки панели). Django сам приводит подпись к строке
(``capfirst()``, ``force_str()``, шаблон), а ``capfirst()`` проверяет
``isinstance(x, str)`` — то есть обёртка **не должна** быть строкой, иначе
она вернула бы исходный русский текст.

``LazyChoice`` — подстрока ``str`` для подписей ``choices``. Здесь наоборот:
значением объекта остаётся исходная русская строка, а переводится только
вывод (``str()``/``format()``). Это нужно потому, что подписи ``choices``
используются и как строки: ``portal/datasets.py`` склеивает их
(``" · ".join(...)``), а миграции записывают их через ``StringSerializer``.
Побочный эффект полезен: при ``makemigrations`` язык вообще не важен —
сериализуется исходное значение.

Безопасность для миграций. ``django.db.migrations.serializer`` для
``Promise`` записывает результат ``str()``, а ``Options.original_attrs``
остаётся нетронутым, поэтому ``makemigrations`` новых миграций не видит
(проверяется тестом ``AdminLabelTest.test_no_new_migrations``).

Порядок поиска перевода — ``tr_admin()``: сначала ``ADMIN_LABELS``, затем
``LABELS`` без учёта регистра (см. ``portal/admin_labels.py``).
"""

from django.apps import apps
from django.utils.functional import Promise

from .admin_labels import ADMIN_LABELS
from .i18n import DEFAULT_LANG, LABELS, active_lang, tr_value

#: Индексы «нижний регистр -> перевод». Строятся один раз, при первом
#: обращении: словари большие, а поиск идёт на каждый вывод подписи.
_CI_ADMIN = None
_CI_LABELS = None

#: Справочники — закрытые перечни (страны, валюты, единицы измерения, типы
#: документов, отрасли, категории товаров). Их наименования панель выводит
#: через ``__str__``, поэтому он тоже переводится.
REFERENCE_MODELS = ("Country", "Currency", "Uom", "DocType", "Industry",
                    "GoodCategory")


def _ci_admin():
    global _CI_ADMIN
    if _CI_ADMIN is None:
        _CI_ADMIN = {}
        for key, pair in ADMIN_LABELS.items():
            _CI_ADMIN.setdefault(key.lower(), pair)
    return _CI_ADMIN


def _ci_labels():
    global _CI_LABELS
    if _CI_LABELS is None:
        _CI_LABELS = {}
        for key, pair in LABELS.items():
            _CI_LABELS.setdefault(key.lower(), pair)
    return _CI_LABELS


def tr_admin(text, lang):
    """Переводит подпись админ-панели. Неизвестная строка — как есть.

    Первый шаг — точное совпадение в ``ADMIN_LABELS`` (там же лежат
    намеренные исключения из ``OVERRIDES``). Второй — ``LABELS`` без учёта
    регистра: подписи моделей строчные, подписи страниц заглавные, но
    означают одно и то же слово.
    """
    if not text or lang == DEFAULT_LANG or not isinstance(text, str):
        return text
    pair = ADMIN_LABELS.get(text) or _ci_admin().get(text.lower())
    if pair is None:
        pair = LABELS.get(text) or _ci_labels().get(text.lower())
    if pair is None:
        return text
    return pair[0] if lang == "zh" else pair[1]


class LazyRu(Promise):
    """Подпись, которая переводится при приведении к строке.

    Не строка — и это существенно: ``capfirst()`` и шаблоны вызывают
    ``str()``, а ``isinstance(x, str)`` даёт False и заставляет их это
    сделать. ``Promise`` в базе нужен миграциям: сериализатор распознаёт
    такие объекты и записывает ``str()``.
    """

    __slots__ = ("ru",)

    def __init__(self, ru):
        self.ru = ru

    def __str__(self):
        return tr_admin(self.ru, active_lang())

    def __repr__(self):
        return "LazyRu(%r)" % (self.ru,)

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(self.ru)

    def __bool__(self):
        return bool(self.ru)

    def __len__(self):
        return len(str(self))

    def __mod__(self, other):
        return str(self) % other

    def __add__(self, other):
        return str(self) + other

    def __radd__(self, other):
        return other + str(self)

    def __format__(self, spec):
        return format(str(self), spec)

    def __getattr__(self, name):
        # .lower()/.capitalize()/.replace()/… — как у строки
        return getattr(str(self), name)


class LazyChoice(str):
    """Подпись перечисления: значение остаётся строкой, вывод переводится.

    В отличие от ``LazyRu``, исходная русская строка — это и есть значение
    объекта, поэтому склейка, сравнение и запись в миграции работают с ней.
    Переводятся только ``str()`` и ``format()`` — то есть вывод в шаблоне.
    """

    def __new__(cls, ru):
        return super().__new__(cls, ru)

    def __str__(self):
        return tr_admin(str.__str__(self), active_lang())

    def __format__(self, spec):
        return format(str(self), spec)

    @property
    def raw(self):
        """Исходная русская строка — для самопроверки словаря."""
        return str.__str__(self)


def _wrap(obj, attr):
    """Оборачивает строковый атрибут в ленивую подпись. True — если обернул."""
    value = getattr(obj, attr, None)
    if isinstance(value, str) and not isinstance(value, LazyChoice) and value:
        setattr(obj, attr, LazyRu(value))
        return True
    return False


def _wrap_pairs(pairs):
    """Оборачивает список пар «значение — подпись». Возвращает (список, был ли)."""
    out, changed = [], False
    for value, label in pairs:
        if (isinstance(label, str) and label
                and not isinstance(label, LazyChoice)):
            out.append((value, LazyChoice(label)))
            changed = True
        else:
            out.append((value, label))
    return out, changed


def _wrap_choices(field):
    """Оборачивает подписи ``choices``. True — если обернул.

    Поддерживаются оба вида: плоский список пар и сгруппированный
    («группа, [пары]»). Перечисляемые классы (``TextChoices``) и вызываемые
    наборы пропускаются: у них подписи уже ленивые либо зависят от данных.
    """
    choices = getattr(field, "choices", None)
    if not choices or isinstance(choices, type) or callable(choices):
        return False
    try:
        items = list(choices)
    except TypeError:
        return False

    out, changed = [], False
    for item in items:
        if not (isinstance(item, (list, tuple)) and len(item) == 2):
            out.append(item)
            continue
        value, label = item
        if isinstance(label, (list, tuple)):
            # сгруппированные значения: (группа, [(значение, подпись), …])
            group, group_changed = _wrap_pairs(label)
            out.append((value, group))
            changed = changed or group_changed
        elif (isinstance(label, str) and label
                and not isinstance(label, LazyChoice)):
            out.append((value, LazyChoice(label)))
            changed = True
        else:
            out.append(item)
    if changed:
        field.choices = out
    return changed


def _localize_str(model):
    """Оборачивает ``__str__`` справочника. True — если обернул."""
    original = model.__str__
    if getattr(original, "_portal_lazy", False):
        return False

    def __str__(self):
        return tr_value(original(self), active_lang())

    __str__._portal_lazy = True
    model.__str__ = __str__
    return True


def localize():
    """Оборачивает подписи приложения, моделей, полей и перечислений.

    Вызывается один раз из ``PortalConfig.ready()``. Повторный вызов
    безвреден: обёрнутые подписи не являются строками (``LazyRu``) либо
    уже помечены (``LazyChoice``), поэтому второй раз не оборачиваются.
    Возвращает число обёрнутых подписей (используется в самопроверке).
    """
    count = 0
    config = apps.get_app_config("portal")
    count += _wrap(config, "verbose_name")
    for model in config.get_models():
        meta = model._meta
        count += _wrap(meta, "verbose_name")
        count += _wrap(meta, "verbose_name_plural")
        for field in meta.get_fields():
            count += _wrap(field, "verbose_name")
            count += _wrap(field, "help_text")
            count += _wrap_choices(field)
        if model.__name__ in REFERENCE_MODELS:
            count += _localize_str(model)
    return count
