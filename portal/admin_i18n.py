# -*- coding: utf-8 -*-
"""管理面板标签的惰性翻译。

Django 用模型元数据构建面板标签：应用的 ``verbose_name``
（``portal/apps.py``）、模型和字段（``portal/models.py``）、
``choices`` 标签（状态、文档种类、计量单位），以及
``site_header`` / ``index_title`` (``portal/admin.py``)。它们全部
以俄语指定，不随界面语言变化——因此选择中文时，
面板外壳会被翻译（其译文包含在 Django 供货中），
而模型、字段和值的名称仍是俄语。

解决办法是把标签包进惰性包装器，它在**输出
的时刻**、即所选语言环境激活时才翻译。包装器有两个，因为对它们的
要求各不相同。

``LazyRu`` ——标签用的 ``Promise`` 包装器（``verbose_name``、
``help_text``、面板标题）。Django 自己会把标签转成字符串
（``capfirst()``、``force_str()``、模板），而 ``capfirst()`` 会检查
``isinstance(x, str)``——也就是说包装器**不能**是字符串，否则
它会返回原始的俄语文本。

``LazyChoice`` ——``choices`` 标签用的 ``str`` 子类。这里恰好相反：
对象的值保持为原始俄语字符串，被翻译的只是
输出（``str()``/``format()``）。这样做是必要的，因为 ``choices``
标签也会被当作字符串使用：``portal/datasets.py`` 会拼接它们
（``" · ".join(...)``），而迁移通过 ``StringSerializer`` 写入它们。
这个副作用是有用的：``makemigrations`` 时语言完全无关紧要——
序列化的是原始值。

对迁移安全。``django.db.migrations.serializer`` 对
``Promise`` 写入 ``str()`` 的结果，而 ``Options.original_attrs``
保持原样，因此 ``makemigrations`` 看不到任何新迁移
（由测试 ``AdminLabelTest.test_no_new_migrations`` 验证）。

译文查找顺序是 ``tr_admin()``：先 ``ADMIN_LABELS``，然后
是忽略大小写的 ``LABELS``（见 ``portal/admin_labels.py``）。

有两个标签面板不是存在元数据里，而是**存在数据库里**，它们同样
会展示给用户：

* ``Permission.name`` ——``migrate`` 时会向其中写入
  「Can add <verbose_name_raw>」，也就是永远的俄语模型名
  （``tr_permission()`` 会从 ``codename`` 重新拼出标签）；
* ``LogEntry.change_message`` ——包含被修改字段名称的 JSON，
  在编辑时刻被冻结（``tr_change_message()`` 会在 Django 拼句之前
  替换它们）。

两个包装器都由同一个 ``localize()`` 启用。

第三组标签同样不经过应用元数据——
它们是**自动创建的 M2M 关系模型**（``Dialog.participants``、
``User.groups`` 等）。Django 从可翻译字符串拼出它们的 ``verbose_name``
并在导入 ``models.py`` 时——此时默认语言环境处于激活状态——就替换好
模型名和字段名：得到的是普通俄语字符串「关系 dialog-user」，
惰性翻译对它已不起作用。
此外，这类模型没有自己的 ``__str__``，因此面板显示的是
服务性的「Dialog_participants object (1)」。这两种问题都能在
删除确认页上看到——见 ``_localize_through_models()``。
"""

import json

from django.apps import apps
from django.utils.functional import Promise
from django.utils.translation import gettext

from .admin_labels import ADMIN_LABELS
from .i18n import DEFAULT_LANG, LABELS, active_lang, tr_value

#: 「小写 -> 译文」的索引。只构建一次，即在首次
#: 访问时：字典很大，而每次输出标签都要做查找。
_CI_ADMIN = None
_CI_LABELS = None

#: 字典是封闭的枚举（国家、货币、计量单位、文档
#: 类型、行业、商品类别）。它们的名称由面板
#: 通过 ``__str__`` 输出，因此 ``__str__`` 也要翻译。
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
    """翻译管理面板标签。未知字符串原样返回。

    第一步是在 ``ADMIN_LABELS`` 中精确匹配（其中也保存着
    有意设置的 ``OVERRIDES`` 例外）。第二步是忽略大小写的
    ``LABELS``：模型标签是小写，页面标签是首字母大写，但
    指的是同一个词。
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
    """在转为字符串时才翻译的标签。

    它不是字符串——这一点很重要：``capfirst()`` 和模板会调用
    ``str()``，而 ``isinstance(x, str)`` 返回 False，从而迫使它们
    这么做。``Promise`` 基类是迁移所需要的：序列化器会识别
    这类对象并写入 ``str()``。
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
        # .lower()/.capitalize()/.replace()/… ——与字符串相同
        return getattr(str(self), name)


class LazyChoice(str):
    """枚举的标签：值仍是字符串，输出被翻译。

    与 ``LazyRu`` 不同，原始俄语字符串本身就是对象的值，
    因此拼接、比较以及写入迁移都直接作用于它。
    只有 ``str()`` 和 ``format()`` 被翻译——即模板中的输出。
    """

    def __new__(cls, ru):
        return super().__new__(cls, ru)

    def __str__(self):
        return tr_admin(str.__str__(self), active_lang())

    def __format__(self, spec):
        return format(str(self), spec)

    @property
    def raw(self):
        """原始俄语字符串——用于字典的自检。"""
        return str.__str__(self)


def _wrap(obj, attr):
    """把字符串属性包装成惰性标签。返回 True 表示已包装。"""
    value = getattr(obj, attr, None)
    if isinstance(value, str) and not isinstance(value, LazyChoice) and value:
        setattr(obj, attr, LazyRu(value))
        return True
    return False


def _wrap_pairs(pairs):
    """包装「值 — 标签」对的列表。返回（列表, 是否包装）。"""
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
    """包装 ``choices`` 标签。返回 True 表示已包装。

    两种形式都支持：扁平的对列表和分组形式
    （「组, [对]」）。枚举类（``TextChoices``）和可调用的
    集合会被跳过：它们的标签已是惰性的，或依赖数据。
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
            # 分组值：(组, [(值, 标签), …])
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
    """把字典的 ``__str__`` 包装起来。返回 True 表示已包装。"""
    original = model.__str__
    if getattr(original, "_portal_lazy", False):
        return False

    def __str__(self):
        return tr_value(original(self), active_lang())

    __str__._portal_lazy = True
    model.__str__ = __str__
    return True


#: 标准权限的动词：``codename`` -> Django 供货中的 msgid。
#: 用的是 msgid 而不是现成译文：``gettext()`` 填入的正是
#: 面板标注自身链接所用的那个词（添加 / 增加 / Add），
#: 因此不必自己编造译文，它也不会与面板不一致。
PERMISSION_VERBS = {"add": "Add", "change": "Change",
                    "delete": "Delete", "view": "View"}


def tr_permission(perm):
    """当前语言下的权限标签。

    ``Permission.name`` 是普通的数据库字段：``migrate`` 时会向其中
    写入「Can add <verbose_name_raw>」，并以俄语存储，
    不随界面语言变化。Django 特意取未翻译的名称，
    为的是让数据不依赖语言环境——但在面板中这种
    标签是用户看得见的，因此在用户页和组页上，
    中文页眉旁边出现了「Can add 附件」这样的列表。

    标签从 ``codename`` 重新拼出：动词用 Django 自带的
    翻译目录翻译，模型名取自其 ``verbose_name``（它
    已被包装、能翻译）。非标准权限
    （``Meta.permissions``）和不存在的模型按数据库中的
    原样返回——它们的 ``codename`` 无法拆解出动作和模型。
    """
    name = perm.name
    action, sep, rest = (perm.codename or "").partition("_")
    verb = PERMISSION_VERBS.get(action)
    if not sep or verb is None:
        return name
    model = perm.content_type.model_class()
    if model is None or rest != model._meta.model_name:
        return name
    return "%s %s" % (gettext(verb), model._meta.verbose_name)


def _localize_permission():
    """翻译权限标签（``Permission`` 模型的 ``__str__``）。"""
    from django.contrib.auth.models import Permission

    original = Permission.__str__
    if getattr(original, "_portal_lazy", False):
        return False

    def __str__(self):
        return "%s | %s" % (self.content_type, tr_permission(self))

    __str__._portal_lazy = True
    Permission.__str__ = __str__
    return True


def tr_change_message(raw):
    """翻译日志消息内部的字段名和模型名。

    ``LogEntry.change_message`` 存储含被修改字段名称的 JSON。
    它们在编辑时刻写入，因此是俄语；Django 会把消息
    整体翻译（``gettext``），但翻译目录里没有俄语字段名，
    因此中文面板里出现了「已修改状态 和 签署
    日期」。名称在格式化**之前**就被替换——句子本身
    由 Django 自己拼出，已经是对的语言。

    不是 JSON 的字符串（日志也能保存简单的
    消息）原样返回。
    """
    if not raw or not raw.startswith("["):
        return raw
    try:
        data = json.loads(raw)
    except ValueError:
        return raw
    lang = active_lang()
    for item in data:
        if not isinstance(item, dict):
            continue
        for block in item.values():
            if not isinstance(block, dict):
                continue
            if block.get("name"):
                block["name"] = tr_admin(block["name"], lang)
            if isinstance(block.get("fields"), list):
                block["fields"] = [tr_admin(f, lang) for f in block["fields"]]
    return json.dumps(data)


def _localize_log_entry():
    """翻译操作日志消息（``get_change_message``）。"""
    from django.contrib.admin.models import LogEntry

    original = LogEntry.get_change_message
    if getattr(original, "_portal_lazy", False):
        return False

    def get_change_message(self):
        if active_lang() == DEFAULT_LANG:
            return original(self)
        # 该方法会读取 self.change_message，因此我们在调用期间
        # 把它临时换掉并返回原值：对象本身不变。
        raw = self.change_message
        self.change_message = tr_change_message(raw)
        try:
            return original(self)
        finally:
            self.change_message = raw

    get_change_message._portal_lazy = True
    LogEntry.get_change_message = get_change_message
    return True


#: 自动创建的 M2M 关系模型标签的开头。Django 用可翻译
#: 字符串「%(from)s-%(to)s relationship」拼出它，并在导入
#: ``models.py`` 时就替换好模型名和字段名（见 ``tr_through_label``）。
THROUGH_HEADS = ("Связь", "Связи")


def tr_through_label(text, lang):
    """M2M 关系的标签：翻译的是词，其余部分是技术名称。

    自动创建模型的标签形如「关系 dialog-user」：第一个
    词是界面词（我们翻译的正是它），「dialog-user」是模型
    和字段的名称，在所有语言下相同，保持原样。
    """
    head, sep, tail = text.partition(" ")
    if sep and head in THROUGH_HEADS:
        return tr_admin(head, lang) + sep + tail
    return tr_admin(text, lang)


class LazyThrough(LazyRu):
    """自动创建的 M2M 关系模型的标签（见 ``tr_through_label``）。"""

    __slots__ = ()

    def __str__(self):
        return tr_through_label(self.ru, active_lang())


def _wrap_through(obj, attr):
    """包装关系标签。返回 True 表示已包装。"""
    value = getattr(obj, attr, None)
    if isinstance(value, str) and not isinstance(value, LazyRu) and value:
        setattr(obj, attr, LazyThrough(value))
        return True
    return False


def _localize_through_str(model):
    """M2M 关系的 ``__str__``：「<对象> — <对象>」而不是「… object (1)」。

    自动创建的模型没有自己的 ``__str__``，继承下来的是
    ``Model.__str__`` ——形如「Dialog_participants
    object (1)」的服务性 ``repr``。在删除确认页上，Django 正是通过
    ``str()`` 列出关联对象，因此用户看到的
    是带行号的技术类名，而不是「这是哪个对话、
    谁是它的参与者」。
    """
    original = model.__str__
    if getattr(original, "_portal_lazy", False):
        return False

    def __str__(self):
        parts = []
        for field in self._meta.fields:
            if not field.is_relation or not field.many_to_one:
                continue
            if getattr(self, field.attname, None) is None:
                continue
            try:
                parts.append(str(getattr(self, field.name)))
            except Exception:                              # noqa: BLE001
                continue
        return " — ".join(parts) if parts else original(self)

    __str__._portal_lazy = True
    model.__str__ = __str__
    return True


def _localize_through_models():
    """自动创建的 M2M 关系模型的标签和 ``__str__``。

    ``AppConfig.get_models()`` 不返回它们（``include_auto_created``
    默认为 ``False``），因此 ``localize()`` 会跳过它们——但它们
    在删除确认页上是可见的。中文面板里显示为

        dialog-user 关系: 2
        dialog-user 关系: Dialog_participants object (1)

    即俄语标签与中文并列，还有服务性的类名。
    """
    count = 0
    seen = set()
    for config in apps.get_app_configs():
        for model in config.get_models():
            for field in model._meta.many_to_many:
                through = field.remote_field.through
                if through in seen or not through._meta.auto_created:
                    continue
                seen.add(through)
                meta = through._meta
                count += _wrap_through(meta, "verbose_name")
                count += _wrap_through(meta, "verbose_name_plural")
                count += _localize_through_str(through)
    return count


def localize():
    """包装应用、模型、字段和枚举的标签。

    从 ``PortalConfig.ready()`` 调用一次。重复调用
    无害：已包装的标签要么不是字符串（``LazyRu``），要么
    已带标记（``LazyChoice``），因此不会被再次包装。
    返回被包装标签的数量（用于自检）。
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
    count += _localize_through_models()
    count += _localize_permission()
    count += _localize_log_entry()
    return count
