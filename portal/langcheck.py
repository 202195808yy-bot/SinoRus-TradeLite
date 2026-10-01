# -*- coding: utf-8 -*-
"""翻译字典的自检。

检查五项相互独立的内容：

* ``scan()``——在当前数据上运行 ``portal/datasets.py`` 的全部提供器，
  收集没有译文的**块标签**；
* ``enum_labels()``——从 ``portal/models.py`` 模型的 ``choices`` 收集**枚举**。
  它们作为值进入单元格（状态、文档类型、
  计量单位），但从语义上讲属于界面，
  因此也应在字典中；
* ``reference_values()``——**字典值**（国家、货币、
  计量单位、文档类型、行业、商品类别）；
* ``admin_labels()``——**管理面板标签**（应用、模型和字段的
  ``verbose_name``，外加 ``help_text``）。面板从 ORM 元数据获取它们，
  而非来自页面提供器，因此单独检查；
* ``through_labels()``——**自动创建的 M2M 关联模型**的标签
  （«Связь dialog-user»）。它们不在 ``get_models()`` 中，
  但在删除确认页面上可见，因此用单独的列表检查。

第二项检查很重要：``scan()`` 只能看到标签，而枚举
以单元格值的形式出现。在只检查标签的年代，101 个
``choices`` 标签一直未翻译，却无人察觉。

供测试 ``portal/tests_i18n.py`` 和工具
``tools/check_lang.py`` 使用。
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

#: 有意不翻译的枚举。
#: Incoterms 术语——国际通用缩写，在各种语言中相同；
#: 语言名称用各自的语言书写；Push 是通知渠道的名称。
ENUM_SKIP = {"CIF", "CPT", "DAP", "DDP", "EXW", "FCA",
             "Русский", "中文", "Push"}


def anon_request(path="/", **params):
    """占位请求：提供器只读取 ``request.user`` 和 ``GET``。"""
    request = RequestFactory().get(path, params)
    request.user = AnonymousUser()
    request.LANG = DEFAULT_LANG
    return request


def _raw_label(label):
    """枚举的原始（俄语）标签。

    ``choices`` 标签被包装为 ``admin_i18n.LazyChoice``——一种字符串，
    在输出时才翻译（``portal/admin_i18n.py``）。要与字典
    核对，需要的是原始字符串，否则检查会把译文
    与字典的键作比较。
    """
    raw = getattr(label, "raw", None)
    if raw is not None:
        return raw
    return label if isinstance(label, str) else str(label)


def enum_labels():
    """应用模型的全部 ``choices`` 标签（``ENUM_SKIP`` 除外）。"""
    out = set()
    for model in apps.get_app_config("portal").get_models():
        for field in model._meta.get_fields():
            for _value, label in (getattr(field, "choices", None) or []):
                if isinstance(label, (list, tuple)):
                    continue
                label = _raw_label(label)
                if label not in ENUM_SKIP:
                    out.add(label)
    return out


def untranslated_enums():
    """``choices`` 中没有译文的枚举。"""
    return {s for s in enum_labels() if s not in LABELS}


#: 字典数据：模型 -> 存放俄语名称的字段。
#: 小型封闭列表（国家、货币、计量单位、文档
#: 类型、行业、商品类别）。它们的名称会
#: 作为值进入单元格，因此按与枚举相同的方式检查。
REFERENCE_FIELDS = (
    ("Country", "name_ru"),
    ("Currency", "name_ru"),
    ("Uom", "name_ru"),
    ("DocType", "name_ru"),
    ("Industry", "name_ru"),
    ("GoodCategory", "name_ru"),
)


def reference_values():
    """应包含在翻译字典中的字典值。"""
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
    """没有译文的字典值。"""
    return {s for s in reference_values() if s not in LABELS}


def reference_mismatches():
    """翻译字典与字典数据自身中文名称之间的不一致。

    字典数据有自己的 ``name_zh`` 字段（见 ``seed_demo``），
    而译文取自翻译字典。两个来源不应有出入，
    因此对值进行核对；模型列表取自
    ``REFERENCE_FIELDS``，但只检查其中有 ``name_zh`` 的那些。

    返回 ``(模型, name_ru, 数据库中, 字典中)`` 列表。
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
                continue                      # 由 untranslated_* 捕获
            if pair[0] != name_zh:
                out.append((model_name, str(name_ru), name_zh, pair[0]))
    return out


#: 管理面板的标签。面板并非从页面提供器
#: 获取它们，而是从 ORM 元数据获取：应用、模型和字段的 ``verbose_name``，
#: 外加 ``help_text``。它们被包装成延迟翻译
#: （``portal/admin_i18n.py``），因此单独检查。
def _raw_text(value):
    """标签的原始字符串。

    标签被包装：``LazyRu``（非字符串）和 ``LazyChoice``（``str``
    的子类）在输出时才翻译。要与字典核对，需要原始的
    俄语字符串，否则检查会把译文与字典的键作比较。
    """
    for attr in ("ru", "raw"):
        raw = getattr(value, attr, None)
        if isinstance(raw, str):
            return raw
    return value if isinstance(value, str) else None


def admin_labels():
    """面板从 ORM 元数据获取的全部俄语标签。

    遍历具体字段（``_meta.fields`` + ``_meta.many_to_many``）：
    反向关联具有形如
    «order line» 的自动英文标签，面板不会将其作为字段标签显示。
    """
    out = set()
    config = apps.get_app_config("portal")
    values = [config.verbose_name]
    for model in config.get_models():
        meta = model._meta
        values += [meta.verbose_name, meta.verbose_name_plural]
        for field in list(meta.fields) + list(meta.many_to_many):
            values += [getattr(field, "verbose_name", None),
                       getattr(field, "help_text", None)]
    for value in values:
        raw = _raw_text(value)
        if raw:
            out.add(raw)
    return out


def untranslated_admin_labels():
    """没有译文的面板标签。"""
    from .admin_i18n import tr_admin

    return {s for s in admin_labels() if tr_admin(s, "zh") == s}


def through_labels():
    """自动创建的 M2M 关联模型的标签（所有应用）。

    ``AppConfig.get_models()`` 不返回这类模型
    （``include_auto_created`` 默认为 ``False``），但面板
    会显示它们：Django 在删除确认页面上列出关联
    对象——«Связи dialog-user: 2»。该标签是复合的
    （«Связь» 加上模型名和字段名），因此它的翻译方式
    与普通面板标签不同，需单独检查。
    """
    out = set()
    seen = set()
    for config in apps.get_app_configs():
        for model in config.get_models():
            for field in model._meta.many_to_many:
                through = field.remote_field.through
                if through in seen or not through._meta.auto_created:
                    continue
                seen.add(through)
                for attr in ("verbose_name", "verbose_name_plural"):
                    raw = _raw_text(getattr(through._meta, attr, None))
                    if raw:
                        out.add(raw)
    return out


def untranslated_through_labels():
    """没有译文的 M2M 关联标签。"""
    from .admin_i18n import tr_through_label

    return {s for s in through_labels() if tr_through_label(s, "zh") == s}


def admin_overrides():
    """面板译文与页面译文不一致的字符串。

    标签先在 ``ADMIN_LABELS`` 中查找，然后不区分大小写地在 ``LABELS``
    中查找，因此只有显式例外（``ADMIN_LABELS.OVERRIDES``）
    才可能出现不一致——例如，«Создан» 在页面上是
    状态（«已创建»），而在模型上是链接标签（«创建人»）。

    返回 ``{字符串: (面板中, 页面中)}``；键的集合必须
    与 ``OVERRIDES`` 一致——否则说明译文悄悄发生了分歧。
    """
    from .admin_labels import ADMIN_LABELS

    ci = {}
    for key, pair in LABELS.items():
        ci.setdefault(key.lower(), (key, pair))

    out = {}
    for key, pair in ADMIN_LABELS.items():
        row = ci.get(key.lower())
        if row and row[1][0] != pair[0]:
            out[key] = (pair[0], row[1][0])
    return out


def provider_pk(fn):
    """带参数页面所用的第一个对象的 pk（或 None）。"""
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
    """运行提供器并返回（全部标签, 未翻译标签）。

    无法执行（缺少数据）的提供器会被跳过，
    并计入计数器。
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
    """已收集块中未翻译的标签。"""
    return {s for s in label_strings(blocks) if s not in LABELS}
