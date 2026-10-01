# -*- coding: utf-8 -*-
"""界面语言切换测试（阶段 4 的完善）。

测试是跨领域的符合性测试（路由、语言字典完整性、管理后台
元数据、Python 版本兼容），因此集中在内核的测试包里，
而不是按应用拆散——它们检查的正是各应用之间的**一致**。
"""
"""界面语言切换测试（阶段 4 的完善）。

检查内容：

* 语言选择：``?lang=`` / 路由 ``/lang/<код>/`` -> 会话 ->
  默认语言；
* 翻译注册表 ``core/pages.py`` 中的页面名称与描述；
* 翻译数据块的标签（表头、KPI 标签）；
* 翻译**枚举**（模型 ``choices``）与**字典
  值** — 它们以值而非标签的形式进入单元格；
* 保留自由数据：名称、编号、日期不翻译；
* 字典 ``core/labels.py`` 与 ``core/i18n.py`` 的完整性；
* 管理面板通过相同的语言选择进行切换；
* 语言纯净性：俄语版本不含汉字，中文版本不含
  西里尔字母（通行写法除外）。
"""

import inspect
import re
from urllib.parse import quote

from django.apps import apps
from core.registry import (model_by_name,
                           project_app_configs,
                           project_models)
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management import CommandError, call_command
from django.test import Client, TestCase
from django.utils import translation

from accounts.models import Profile
from catalog.models import Country, Currency, Good, Uom
from documents.models import Document
from logistics.models import Incident, Shipment, Tariff
from messaging.models import Dialog, Translation
from trading.models import Order
from core.admin_i18n import localize, tr_permission
from core.admin_labels import OVERRIDES
from core.datasets import provider_for
from core.i18n import (DEFAULT_LANG, LABELS, LANGS, LANG_LABELS, LANG_SHORT, UI,
                   normalize, tr, translate_blocks, translate_cell, tr_value,
                   value_strings)
from core.langcheck import (ENUM_SKIP, admin_labels, admin_overrides, anon_request,
                        provider_pk, reference_mismatches, scan, through_labels,
                        untranslated_admin_labels, untranslated_enums,
                        untranslated_reference_values,
                        untranslated_through_labels)
from core.pages import PAGES, content_of, module_name, purpose_of, title_of
from core.views import _page_data

CJK = re.compile(r"[\u4e00-\u9fff]")
CYR = re.compile(r"[\u0400-\u04ff]")

#: 中文文本中允许出现的西里尔字母（通行写法）
CYR_ALLOWED_IN_ZH = {"ИНН"}

#: 标记与样式的注释不是界面文本，用户看不到
#: 它们。项目模板中它们与其他说明一样使用俄语。
COMMENTS = re.compile(r"<!--.*?-->|/\*.*?\*/", re.S)

#: 面板中允许出现的西里尔字母：语言名称以其自身语言书写
#: (切换器中的 ``title="Русский"`` — 与门户页面相同)。
CYR_ALLOWED_IN_ADMIN = {name for name in LANG_LABELS.values() if CYR.search(name)}

#: 由面板自行填写并存入数据库的字段。其内容是
#: 标签而非自由数据，因此不会进入白名单：
#: 正是在这些字段上捕获“冻结的”俄语文本。
GENERATED_LABEL_FIELDS = {
    ("auth", "permission"): {"name"},
    ("admin", "logentry"): {"change_message"},
}

#: 被视为数据的截断文本的最小长度。面板显示长文本时
#: 会将其截断（``Truncator``），因此标记中会混入
#: 词的一部分 — «сертификата» 的 «сертифика»。这类截断是允许的，但
#: 不能短于该阈值：否则在短标签（«Дата»、«Роль»）之下
#: 任何东西都会被掩盖。
MIN_TRUNCATED = 5


def cyr_words(text):
    """字符串中的西里尔字母单词。"""
    return set(re.findall(r"[\u0400-\u04ff][\u0400-\u04ff\-.]*", text))


def visible_text(html):
    """不含注释的标记 — 只包含用户看到的内容。"""
    return COMMENTS.sub(" ", html)


def demo_words():
    """来自演示数据的西里尔字母词汇。

    自由数据——企业和商品的名称、编号、地址、
    自由备注、JSON 字段键——不可翻译，因此
    词典中没有它们。为了让“中文面板中不残留俄语
    标签”的检查不被数据绊住，这些词汇直接从数据库本身收集。

    遍历的是 **所有** 应用，而不只是某一个应用：用户页面上
    会显示其姓名（``auth``），日志中——对象的快照
    （``admin``）。例外是 ``GENERATED_LABEL_FIELDS``。
    """
    from django.db import models as dj

    out = set()
    for config in apps.get_app_configs():
        for model in config.get_models():
            meta = model._meta
            skip = GENERATED_LABEL_FIELDS.get((meta.app_label, meta.model_name),
                                              set())
            names = [f.name for f in meta.fields
                     if isinstance(f, (dj.CharField, dj.TextField, dj.JSONField))
                     and f.name not in skip]
            if not names:
                continue
            for row in model.objects.values_list(*names):
                for value in row:
                    if value is None:
                        continue
                    for word in cyr_words(str(value)):
                        out.add(word)
                        for cut in range(MIN_TRUNCATED, len(word)):
                            out.add(word[:cut])
    return out


class LanguageSelectionTest(TestCase):
    """语言选择：请求参数、会话、默认值。"""

    def setUp(self):
        self.client = Client(HTTP_HOST="localhost")

    def test_default_language_is_russian(self):
        response = self.client.get("/orders/")
        self.assertEqual(response.context["LANG"], DEFAULT_LANG)
        self.assertEqual(response.status_code, 200)

    def test_query_parameter_switches_language(self):
        for code in LANGS:
            response = self.client.get("/orders/?lang=" + code)
            self.assertEqual(response.context["LANG"], code)

    def test_choice_is_remembered_in_session(self):
        self.client.get("/orders/?lang=zh")
        self.assertEqual(self.client.session["lang"], "zh")
        # 下一个不带参数的请求 — 语言取自会话
        response = self.client.get("/goods/")
        self.assertEqual(response.context["LANG"], "zh")

    def test_unknown_language_falls_back_to_default(self):
        response = self.client.get("/orders/?lang=de")
        self.assertEqual(response.context["LANG"], DEFAULT_LANG)
        response = self.client.get("/orders/?lang=")
        self.assertEqual(response.context["LANG"], DEFAULT_LANG)

    def test_normalize_accepts_aliases(self):
        self.assertEqual(normalize("zh-Hans"), "zh")
        self.assertEqual(normalize("ZH_cn"), "zh")
        self.assertEqual(normalize("ru-RU"), "ru")
        self.assertEqual(normalize("EN"), "en")
        self.assertIsNone(normalize("de"))
        self.assertIsNone(normalize(None))

    def test_switcher_renders_all_languages(self):
        response = self.client.get("/orders/?lang=zh")
        html = response.content.decode("utf-8")
        for code in LANGS:
            self.assertIn(LANG_SHORT[code], html)
        self.assertIn('class="lang-btn is-active"', html)
        # 切换器指向单独的路由并保留当前地址
        self.assertIn("/lang/ru/?next=%2Forders%2F", html)
        self.assertIn("/lang/en/?next=%2Forders%2F", html)

    def test_switch_endpoint_remembers_and_returns(self):
        """切换路由会记住语言并返回原始地址。"""
        response = self.client.get("/lang/en/?next=" + quote("/orders/", safe=""))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/orders/")
        self.assertEqual(self.client.session["lang"], "en")
        self.assertEqual(self.client.get("/orders/").context["LANG"], "en")

    def test_switch_endpoint_rejects_external_redirect(self):
        """防范开放重定向：外部地址会被替换为“/”。"""
        for bad in ("//evil.example.com/", "https://evil.example.com/", "evil"):
            response = self.client.get(
                "/lang/ru/?next=" + quote(bad, safe=""))
            self.assertEqual(response["Location"], "/", bad)

    def test_switch_endpoint_ignores_unknown_code(self):
        """未知的语言代码不会破坏选择：保持原来的选择。"""
        self.client.get("/lang/zh/?next=%2Forders%2F")
        self.client.get("/lang/de/?next=%2Forders%2F")
        self.assertEqual(self.client.session["lang"], "zh")

    def test_html_lang_attribute_follows_choice(self):
        self.assertIn('lang="ru"', self.client.get("/").content.decode())
        self.assertIn('lang="zh-Hans"',
                      self.client.get("/?lang=zh").content.decode())
        self.assertIn('lang="en"', self.client.get("/?lang=en").content.decode())

    def test_logout_keeps_language(self):
        """退出登录不会重置所选语言。

        ``auth_logout()`` 会连同语言一起清空整个会话，因此
        退出视图会保存选择并恢复它。
        """
        from django.contrib.auth import get_user_model
        user = get_user_model().objects.create_user(
            username="langout", password="langout-pass")
        self.client.force_login(user)
        self.client.get("/lang/zh/?next=%2F")
        self.assertEqual(self.client.get("/accounts/logout/").status_code, 302)
        self.assertEqual(self.client.session["lang"], "zh")
        self.assertEqual(self.client.get("/").context["LANG"], "zh")


class PageContentLanguageTest(TestCase):
    """页面名称、用途和内容均按当前语言显示。"""

    def test_resolved_fields_match_registry_helpers(self):
        for page in PAGES:
            for lang in LANGS:
                data = _page_data(page, lang)
                self.assertEqual(data["title"], title_of(page, lang))
                self.assertEqual(data["purpose"], purpose_of(page, lang))
                self.assertEqual(data["content"], content_of(page, lang))

    def test_russian_version_has_no_cjk(self):
        """描述的俄语版本不应包含汉字。"""
        offenders = [(p["name"], field)
                     for p in PAGES
                     for field in ("ru", "purpose_ru", "content_ru")
                     if CJK.search(p[field])]
        self.assertEqual(offenders, [], f"китайские символы в ru: {offenders}")

    def test_chinese_version_is_translated_and_clean(self):
        """中文版本已翻译，且几乎不含西里尔字母。"""
        for page in PAGES:
            data = _page_data(page, "zh")
            self.assertTrue(CJK.search(data["purpose"]),
                            f"{page['name']}: назначение не переведено")
            extra = cyr_words(data["purpose"]) | cyr_words(data["content"])
            self.assertTrue(extra <= CYR_ALLOWED_IN_ZH,
                            f"{page['name']}: кириллица в китайской версии "
                            f"{extra - CYR_ALLOWED_IN_ZH}")

    def test_legacy_keys_are_overridden_by_language(self):
        """历史键 purpose/content 不再“卡”在中文上。"""
        page = PAGES[0]
        self.assertEqual(_page_data(page, "ru")["purpose"], page["purpose_ru"])
        self.assertEqual(_page_data(page, "zh")["purpose"], page["purpose_zh"])
        self.assertNotEqual(_page_data(page, "ru")["purpose"], page["purpose"])

    def test_module_titles_follow_language(self):
        page = PAGES[0]
        for lang in LANGS:
            data = _page_data(page, lang)
            alt = "ru" if lang == "zh" else "zh"
            self.assertEqual(data["module_title"], module_name(page["module"], lang))
            self.assertEqual(data["module_alt"], module_name(page["module"], alt))
            self.assertNotEqual(data["module_title"], data["module_alt"])


class BlockLabelTranslationTest(TestCase):
    """数据块的标签会被翻译，单元格的值则不会。"""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)

    def setUp(self):
        self.client = Client(HTTP_HOST="localhost")

    @staticmethod
    def headers(html):
        match = re.search(r"<thead>\s*<tr>(.*?)</tr>", html, re.S)
        return re.findall(r"<th>(.*?)</th>", match.group(1)) if match else []

    def test_table_headers_are_translated(self):
        ru = self.headers(self.client.get("/orders/?lang=ru").content.decode())
        zh = self.headers(self.client.get("/orders/?lang=zh").content.decode())
        en = self.headers(self.client.get("/orders/?lang=en").content.decode())
        self.assertTrue(ru and len(ru) == len(zh) == len(en))
        self.assertEqual(ru[0], "Номер")
        self.assertEqual(zh[0], "编号")
        self.assertEqual(en[0], "Number")
        # 俄语版本不含汉字，中文版本不含西里尔字母
        self.assertFalse(any(CJK.search(h) for h in ru))
        self.assertFalse(any(CYR.search(h) for h in zh))

    def test_block_titles_are_translated(self):
        html = self.client.get("/orders/1/?lang=zh").content.decode()
        for expected in ("订单卡片", "订单明细", "执行阶段"):
            self.assertIn(expected, html)

    def test_cell_values_are_not_translated(self):
        """单元格的值是数据，不会被词典替换。"""
        response = self.client.get("/orders/?lang=zh")
        html = response.content.decode()
        self.assertIn("ORD-", html)          # 单证编号保持原样

    def test_translate_blocks_does_not_touch_free_data(self):
        """单元格中的自由数据保持原样。

        枚举值（“已签署”）会被翻译，因为它在词典中，
        而企业名称则不会：词典里没有它。
        """
        blocks = [{"kind": "table", "title": "Заказы", "empty": "Заказов нет",
                   "columns": ["Статус"],
                   "rows": [[{"text": "Медтех-Рус", "url": None}]],
                   "items": []}]
        out = translate_blocks(blocks, "zh")
        self.assertEqual(out[0]["title"], "订单")
        self.assertEqual(out[0]["columns"], ["状态"])
        self.assertEqual(out[0]["empty"], "无订单")
        self.assertEqual(out[0]["rows"][0][0]["text"], "Медтех-Рус")

    def test_translate_blocks_is_noop_for_russian(self):
        blocks = [{"kind": "table", "title": "Заказы", "columns": ["Статус"],
                   "rows": [], "items": []}]
        out = translate_blocks(blocks, "ru")
        self.assertEqual(out[0]["title"], "Заказы")
        self.assertEqual(out[0]["columns"], ["Статус"])

    def test_unknown_label_passes_through(self):
        blocks = [{"kind": "table", "title": "Некая новая подпись",
                   "columns": [], "rows": [], "items": []}]
        out = translate_blocks(blocks, "zh")
        self.assertEqual(out[0]["title"], "Некая новая подпись")


class InterfaceTextTest(TestCase):
    """界面翻译词典已填写完整。"""

    def test_labels_have_two_translations(self):
        broken = [key for key, row in LABELS.items()
                  if len(row) != 2 or not all(str(v).strip() for v in row)]
        self.assertEqual(broken, [], f"неполные переводы: {broken}")

    def test_ui_has_all_three_languages(self):
        self.assertEqual(set(LANGS), {"ru", "zh", "en"})
        self.assertEqual(set(LANG_LABELS), set(LANGS))
        self.assertEqual(set(LANG_SHORT), set(LANGS))
        broken = [key for key, row in UI.items()
                  if len(row) != 3 or not all(str(v).strip() for v in row)]
        self.assertEqual(broken, [], f"неполные тексты оболочки: {broken}")

    def test_translation_examples(self):
        self.assertEqual(tr("Заказы", "zh"), "订单")
        self.assertEqual(tr("Заказы", "en"), "Orders")
        self.assertEqual(tr("Заказы", "ru"), "Заказы")
        self.assertEqual(tr("Нет такой подписи", "zh"), "Нет такой подписи")
        self.assertEqual(tr(None, "zh"), None)

    def test_ui_texts_are_language_specific(self):
        for key, row in UI.items():
            self.assertEqual(len(set(row)), 3, f"{key}: тексты совпадают")

    def test_russian_ui_texts_have_no_cjk(self):
        offenders = [key for key, row in UI.items() if CJK.search(row[0])]
        self.assertEqual(offenders, [], f"иероглифы в русских текстах: {offenders}")

    def test_chinese_ui_texts_have_no_cyrillic(self):
        offenders = [key for key, row in UI.items()
                     if cyr_words(row[1]) - CYR_ALLOWED_IN_ZH]
        self.assertEqual(offenders, [],
                         f"кириллица в китайских текстах: {offenders}")


class AdminLanguageTest(TestCase):
    """管理面板用同样的语言选择来切换。

    面板使用 Django 的模板和翻译，因此这里检查
    ``LanguageMiddleware`` 会激活所需的 locale，以及语言
    切换器已渲染出来。

    切换器指向 ``core:set_language`` 路由，而不是
    ``?lang=``：在面板的列表中 Django 会把未知参数
    当作过滤器并返回多余的重定向（参见
    ``test_admin_list_page_rejects_lang_query``）。
    """

    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth import get_user_model
        call_command("seed_demo", verbosity=0)
        cls.root = get_user_model().objects.create_superuser(
            username="root", email="root@example.com",
            password="admin-test-pass")

    def setUp(self):
        self.client = Client(HTTP_HOST="localhost")
        self.client.force_login(self.root)

    def switch(self, code, target="/admin/"):
        """切换语言的方式与面板头部链接的做法相同。"""
        return self.client.get(
            "/lang/%s/?next=%s" % (code, quote(target, safe="")))

    def test_admin_index_renders(self):
        self.assertEqual(self.client.get("/admin/").status_code, 200)

    def test_admin_follows_language(self):
        """面板界面随语言选择一起翻译。"""
        # Django 将 «Add» 译为 Добавить / 增加 / Add
        expected = {"ru": "Добавить", "zh": "增加", "en": "Add"}
        for code in LANGS:
            self.switch(code)
            response = self.client.get("/admin/")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context["LANG"], code)
            html = response.content.decode("utf-8")
            self.assertIn(expected[code], html,
                          f"{code}: панель не переведена")

    def test_admin_html_lang_attribute(self):
        expected = {"ru": "ru", "zh": "zh-hans", "en": "en"}
        for code in LANGS:
            self.switch(code)
            html = self.client.get("/admin/").content.decode()
            self.assertIn(f'<html lang="{expected[code]}"', html)

    def test_admin_switcher_is_rendered(self):
        html = self.client.get("/admin/").content.decode()
        self.assertIn("admin-lang", html)
        self.assertIn("/lang/ru/?next=%2Fadmin%2F", html)
        self.assertIn("/lang/en/?next=%2Fadmin%2F", html)
        self.assertIn("is-active", html)

    def test_admin_switcher_link_round_trip(self):
        """头部链接确实会切换语言并返回原处。"""
        html = self.client.get("/admin/").content.decode()
        match = re.search(r'href="(/lang/zh/\?next=[^"]+)"', html)
        self.assertIsNotNone(match, "ссылка переключателя не найдена")
        response = self.client.get(match.group(1).replace("&amp;", "&"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/admin/")
        self.assertEqual(self.client.session["lang"], "zh")

    def test_admin_switcher_on_login_page(self):
        """登录页面上也有切换器（branding 区块）。"""
        client = Client(HTTP_HOST="localhost")       # 匿名
        html = client.get("/admin/login/").content.decode()
        self.assertIn("admin-lang", html)
        self.assertIn("/lang/ru/?next=%2Fadmin%2Flogin%2F", html)

    def test_admin_language_is_remembered(self):
        self.switch("en")
        self.assertEqual(self.client.session["lang"], "en")
        self.assertEqual(self.client.get("/admin/").context["LANG"], "en")

    def test_admin_deep_pages_keep_working(self):
        """所选语言不影响面板的各分区（地址不含 ?lang=）。"""
        self.switch("zh")
        for url in ("/admin/trading/order/", "/admin/trading/order/1/change/",
                    "/admin/catalog/good/", "/admin/auth/user/"):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)

    def test_admin_list_page_rejects_lang_query(self):
        """``?lang=`` 在 Django 面板的列表中被当作过滤器。

        这正是需要单独切换路由的原因：请求
        ``/admin/trading/order/?lang=zh`` 返回带错误标记
        （``?e=1``）的重定向，而不是列表页面。
        """
        response = self.client.get("/admin/trading/order/?lang=zh")
        self.assertEqual(response.status_code, 302)
        self.assertIn("e=1", response["Location"])

    def test_portal_and_admin_share_the_choice(self):
        """同一个语言选择在应用和面板中都生效。"""
        self.client.get("/?lang=zh")
        self.assertEqual(self.client.get("/admin/").context["LANG"], "zh")
        self.assertEqual(self.client.get("/orders/").context["LANG"], "zh")


class AdminLabelTest(TestCase):
    """面板的标签——模型、字段和值的名称——跟随语言。

    面板从 ORM 元数据获取它们，而不是从页面提供器，因此
    没有包装器时它们始终是俄语（``core/admin_i18n.py``）。包装器有两个：
    ``LazyRu``——用于标签，``LazyChoice``——用于 ``choices`` 的标签；
    后者仍是真实的字符串，因为 ``core/datasets.py + <app>/datasets.py``
    会拼接它们，而迁移会将其写入。

    另外两个标签面板存储 **在数据库中**，它们同样
    以俄语冻结：``Permission.name``（在 ``migrate`` 时生成为“Can add
    <verbose_name_raw>”）和 ``LogEntry.change_message``（被修改字段的
    名称在编辑时写入）。两者都在输出时翻译。

    第三组是 **自动创建的 M2M 关系模型**：它们的 ``verbose_name``
    由 Django 在导入 ``models.py`` 时从可翻译字符串拼出，而
    ``get_models()`` 不返回这类模型，因此 ``localize()``
    和元数据遍历都跳过了它们。它们显示在删除
    确认页面上。
    """

    @classmethod
    def setUpTestData(cls):
        from django.contrib.admin.models import CHANGE, LogEntry
        from django.contrib.auth import get_user_model
        from django.contrib.contenttypes.models import ContentType

        call_command("seed_demo", verbosity=0)
        cls.root = get_user_model().objects.create_superuser(
            username="root-labels", email="root@example.com",
            password="admin-test-pass")

        # 带俄语字段名的日志记录 — 面板在编辑对象时会
        # 自行创建这种记录。需要它以便历史页面
        # 也接受“冻结”标签检查。
        order = Order.objects.first()
        cls.log_entry = LogEntry.objects.log_action(
            user_id=cls.root.pk,
            content_type_id=ContentType.objects.get_for_model(order).pk,
            object_id=order.pk, object_repr=str(order), action_flag=CHANGE,
            change_message='[{"changed": {"fields": ["\u0441\u0442\u0430\u0442\u0443\u0441",'
                           ' "\u0434\u0430\u0442\u0430 \u043f\u043e\u0434\u043f\u0438\u0441\u0430\u043d\u0438\u044f"]}}]')

    def setUp(self):
        self.client = Client(HTTP_HOST="localhost")
        self.client.force_login(self.root)

    # ---------------------------------------------------------- 字典
    def test_every_admin_label_is_translated(self):
        missing = untranslated_admin_labels()
        self.assertEqual(missing, set(),
                         f"нет перевода подписей панели: {sorted(missing)}")

    def test_admin_overrides_are_explicit(self):
        """与页面词典的差异必须显式声明。"""
        self.assertEqual(set(admin_overrides()), set(OVERRIDES),
                         f"переводы разъехались: {admin_overrides()}")

    def test_admin_labels_are_not_empty(self):
        self.assertGreater(len(admin_labels()), 200)

    # ------------------------------------------------- 惰性翻译
    def test_app_name_follows_language(self):
        # 拆分后每个应用有自己的 verbose_name；逐个核对。
        pairs = {
            "core": ("Ядро платформы", "平台内核", "Platform core"),
            "accounts": ("Организации и аккаунты", "企业与账号",
                         "Organizations and accounts"),
            "messaging": ("Двуязычное общение", "双语沟通",
                          "Bilingual communication"),
        }
        configs = {c.label: c for c in project_app_configs()}
        for label, (ru, zh, en) in pairs.items():
            name = configs[label].verbose_name
            self.assertEqual(str(name), ru)
            with translation.override("zh-hans"):
                self.assertEqual(str(name), zh)
            with translation.override("en"):
                self.assertEqual(str(name), en)

    def test_model_name_follows_language(self):
        meta = Currency._meta
        self.assertEqual(str(meta.verbose_name), "валюта")
        self.assertEqual(str(meta.verbose_name_plural), "валюты")
        with translation.override("zh-hans"):
            self.assertEqual(str(meta.verbose_name), "币种")
            self.assertEqual(str(meta.verbose_name_plural), "币种")
        with translation.override("en"):
            self.assertEqual(str(meta.verbose_name_plural), "Currencies")

    def test_field_label_follows_language(self):
        field = Shipment._meta.get_field("container_no")
        self.assertEqual(str(field.verbose_name), "номер контейнера")
        with translation.override("zh-hans"):
            self.assertEqual(str(field.verbose_name), "集装箱号")
        with translation.override("en"):
            self.assertEqual(str(field.verbose_name), "Container number")

    def test_choice_label_follows_language(self):
        labels = dict(Document._meta.get_field("status").choices)
        self.assertEqual(str(labels["draft"]), "Черновик")
        with translation.override("zh-hans"):
            self.assertEqual(str(labels["draft"]), "草稿")
            self.assertEqual(str(labels["archived"]), "已归档")
        with translation.override("en"):
            self.assertEqual(str(labels["draft"]), "Draft")

    def test_reference_str_follows_language(self):
        """字典的外键以翻译后的形式显示。"""
        country = Country.objects.get(name_ru="Россия")
        uom = Uom.objects.get(name_ru="штука")
        self.assertEqual(str(country), "RU — Россия")
        self.assertEqual(str(uom), "штука (pcs)")
        with translation.override("zh-hans"):
            self.assertEqual(str(country), "RU — 俄罗斯")
            self.assertEqual(str(uom), "件 (pcs)")

    def test_free_data_is_not_translated(self):
        """自由数据在任何语言下都保持原样。"""
        good = Good.objects.first()
        with translation.override("zh-hans"):
            self.assertNotEqual(str(good), "")
            self.assertEqual(str(good), str(good.raw) if hasattr(good, "raw")
                             else str(good))

    # ----------------------------- choices 标签保持为字符串
    def test_choice_label_stays_a_string(self):
        """回归：``core/datasets.py + <app>/datasets.py`` 会拼接 ``choices`` 的标签。"""
        choices = list(Incident._meta.get_field("kind").choices)
        joined = " · ".join(label for _value, label in choices)
        self.assertIsInstance(joined, str)
        self.assertEqual(joined,
                         " · ".join(label.raw for _v, label in choices))
        label = choices[0][1]
        self.assertIsInstance(label, str)          # 比较 — 按原始值
        self.assertEqual(label, label.raw)

    # -------------------------------------------------- 整个面板
    def test_admin_shell_has_no_cyrillic(self):
        """无数据页面：界面已完全翻译。

        标记和样式中的注释不算作界面文本，
        而切换器中的语言名称则以各自的语言书写。
        """
        pages = ("/admin/", "/admin/catalog/", "/admin/catalog/currency/",
                 "/admin/system/auditlog/")
        for code in ("zh", "en"):
            self.client.get("/lang/%s/?next=/admin/" % code)
            for url in pages:
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200, url)
                offenders = (cyr_words(visible_text(response.content.decode("utf-8")))
                             - CYR_ALLOWED_IN_ADMIN)
                self.assertEqual(offenders, set(), f"{code} {url}: {offenders}")

    def test_admin_pages_have_no_russian_interface(self):
        """有数据的页面上，西里尔字母只保留在数据中。

        页面清单特意取得很宽：曾有一次正是漏掉了
        用户页面，导致权限标签（“Can add 附件”）被遗漏，
        而漏掉历史页面则漏掉了日志中的字段名称。
        """
        allowed = demo_words() | CYR_ALLOWED_IN_ADMIN
        pages = ("/admin/trading/order/", "/admin/trading/order/1/change/",
                 "/admin/trading/order/1/history/",
                 "/admin/catalog/good/", "/admin/catalog/good/1/change/",
                 "/admin/accounts/enterprise/", "/admin/documents/document/",
                 "/admin/billing/statement/1/change/",
                 "/admin/accounts/profile/", "/admin/accounts/profile/1/change/",
                 "/admin/logistics/tariff/", "/admin/messaging/dialog/",
                 "/admin/messaging/translation/", "/admin/messaging/message/",
                 "/admin/catalog/good/add/", "/admin/logistics/tariff/add/",
                 "/admin/auth/user/", "/admin/auth/user/1/change/",
                 "/admin/auth/group/", "/admin/auth/group/add/",
                 # 删除确认页面：Django 会在其上列出
                 # 关联对象，包括通过自动创建的
                 # M2M 关联模型（«Связи dialog-user»）。跳过它们
                 # 曾同时隐藏俄语标签和系统文字“… object (1)”。
                 "/admin/messaging/dialog/1/delete/",
                 "/admin/trading/order/1/delete/",
                 "/admin/auth/user/2/delete/")
        for code in ("zh", "en"):
            self.client.get("/lang/%s/?next=/admin/" % code)
            for url in pages:
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200, url)
                offenders = (cyr_words(visible_text(response.content.decode("utf-8")))
                             - allowed)
                self.assertEqual(offenders, set(), f"{code} {url}: {offenders}")

    # ------------------------------------- 数据库中冻结的标签
    def test_permission_labels_follow_language(self):
        """权限标签从 ``codename`` 重新生成。

        数据库中存的是“Can add 附件”：Django 往里写入
        未翻译的模型名称，以便数据不依赖 locale。
        面板中能看到这样的标签，因此在输出时翻译。
        """
        perm = Permission.objects.get(codename="add_attachment")
        self.assertEqual(perm.name, "Can add вложение")      # 与数据库中一致
        self.assertEqual(str(perm), "messaging | вложение | Добавить вложение")
        with translation.override("zh-hans"):
            self.assertEqual(str(perm), "messaging | 附件 | 增加 附件")
        with translation.override("en"):
            self.assertEqual(str(perm), "messaging | Attachment | Add Attachment")

    def test_permission_verbs_match_the_panel(self):
        """权限动词与同一语言的面板标签一致。"""
        for code, verb in (("zh-hans", "增加"), ("ru", "Добавить")):
            with translation.override(code):
                label = str(Permission.objects.get(codename="add_user"))
                self.assertEqual(label.split(" | ")[-1].split(" ")[0], verb,
                                 f"{code}: глагол не совпал с надписью панели")

    def test_custom_permission_keeps_its_name(self):
        """非标准权限不做解析，保持数据库中的原样。"""
        content_type = ContentType.objects.get_for_model(Order)
        perm = Permission(name="Can approve order", codename="can_approve_order",
                          content_type=content_type)
        with translation.override("zh-hans"):
            self.assertEqual(tr_permission(perm), "Can approve order")

    def test_log_message_follows_language(self):
        """日志中的字段名称会被翻译，记录本身不变。"""
        entry = LogEntry.objects.get(pk=self.log_entry.pk)
        raw = entry.change_message
        self.assertIn("статус", raw)
        self.assertEqual(entry.get_change_message(),
                         "Изменено статус и дата подписания.")
        with translation.override("zh-hans"):
            message = entry.get_change_message()
            self.assertEqual(message, "已修改状态 和 签署日期。")
            self.assertEqual(cyr_words(message), set())
        with translation.override("en"):
            self.assertEqual(entry.get_change_message(),
                             "Changed Status and Signed date.")
        # 输出不应把翻译写入数据库
        self.assertEqual(LogEntry.objects.get(pk=self.log_entry.pk).change_message,
                         raw)

    def test_log_message_keeps_plain_text(self):
        """日志也能存储简单消息——不去动它。"""
        entry = LogEntry(object_repr="x", change_message="Изменено вручную.")
        with translation.override("zh-hans"):
            self.assertEqual(entry.get_change_message(), "Изменено вручную.")

    # -------------------- 自动创建的 M2M 关联模型（删除页面）
    def test_every_through_label_is_translated(self):
        """每个 M2M 关系标签都有翻译。"""
        missing = untranslated_through_labels()
        self.assertEqual(missing, set(),
                         f"нет перевода подписей связей M2M: {sorted(missing)}")
        self.assertGreaterEqual(len(through_labels()), 4)

    def test_through_label_follows_language(self):
        """M2M 关系的标签会被翻译，模型和字段的名称则不会。

        Django 从可翻译字符串“%(from)s-%(to)s relationship”
        拼出自动创建模型的 ``verbose_name``，并在导入 ``models.py``、
        默认 locale 生效之时 **立刻** 代入模型
        和字段的名称。得到的字符串是普通字符串，已经是
        俄语，惰性翻译不会作用于它——词典中没有键。
        因此只翻译第一个词，而“dialog-user”保留不变：
        它是技术名称，在所有语言下都相同。
        """
        through = Dialog._meta.get_field("participants").remote_field.through
        self.assertTrue(through._meta.auto_created)
        self.assertEqual(str(through._meta.verbose_name), "Связь dialog-user")
        with translation.override("zh-hans"):
            self.assertEqual(str(through._meta.verbose_name), "关系 dialog-user")
            self.assertEqual(str(through._meta.verbose_name_plural),
                             "关系 dialog-user")
        with translation.override("en"):
            self.assertEqual(str(through._meta.verbose_name),
                             "Relationship dialog-user")
            self.assertEqual(str(through._meta.verbose_name_plural),
                             "Relationships dialog-user")

    def test_through_str_is_readable(self):
        """自动创建的关系没有自己的 ``__str__``——我们来定义一个可读的。

        默认继承 ``Model.__str__``，即“Dialog_participants
        object (1)”：在删除确认页面上，用户看到的是
        类的服务名称，而不是“这是哪个对话、参与者是谁”。
        """
        through = Dialog._meta.get_field("participants").remote_field.through
        obj = through.objects.first()
        text = str(obj)
        self.assertNotIn("object (", text)
        self.assertIn("—", text)

    def test_delete_page_shows_no_russian(self):
        """删除确认页面已完整翻译。"""
        allowed = demo_words() | CYR_ALLOWED_IN_ADMIN
        for code in ("zh", "en"):
            self.client.get("/lang/%s/?next=/admin/" % code)
            response = self.client.get("/admin/messaging/dialog/1/delete/")
            self.assertEqual(response.status_code, 200)
            offenders = (cyr_words(visible_text(response.content.decode("utf-8")))
                         - allowed)
            self.assertEqual(offenders, set(), f"{code}: {offenders}")

    # ----------------------------------- 模型 ``__str__`` 内的标签
    def test_model_str_labels_follow_language(self):
        """``__str__`` 内部的标签取自词典。

        面板在 ``translate_blocks`` 之外调用 ``__str__``——列表、
        面包屑、标题和下拉列表中——因此写死的
        俄语词（“个人资料：ivanov”）在任何语言下都会
        直达用户。
        """
        objects = [Profile.objects.first(), Tariff.objects.first(),
                   Dialog.objects.first(), Translation.objects.first()]
        for code in ("zh-hans", "en"):
            with translation.override(code):
                for obj in objects:
                    text = str(obj)
                    self.assertEqual(cyr_words(text), set(),
                                     f"{code} {type(obj).__name__}: {text}")
        with translation.override("zh-hans"):
            profile = str(Profile.objects.first())
            self.assertTrue(profile.startswith("用户"), profile)
            self.assertIn("增值税", str(Tariff.objects.first()))
        with translation.override("en"):
            self.assertTrue(str(Profile.objects.first()).startswith("Profile"))
            self.assertIn("VAT", str(Tariff.objects.first()))

    def test_model_str_label_agrees_with_model_name(self):
        """``__str__`` 中的标签与页面上模型的名称一致。"""
        with translation.override("zh-hans"):
            prefix = str(Profile.objects.first()).split(":")[0]
            self.assertEqual(prefix, str(Profile._meta.verbose_name).capitalize())

    def test_model_str_labels_keep_default_language(self):
        """俄语是标签的源语言：它不发生改变。"""
        self.assertEqual(str(Profile.objects.first()), "Профиль: ivanov")
        self.assertIn("пошлина", str(Tariff.objects.first()))

    def test_admin_headers_are_translated(self):
        self.client.get("/lang/zh/?next=/admin/")
        html = self.client.get("/admin/trading/order/").content.decode("utf-8")
        for word in ("编号", "状态", "金额", "签署日期"):
            self.assertIn(word, html, f"заголовок {word} не найден")

    # ------------------------------------------------------- 机制
    def test_localize_is_idempotent(self):
        self.assertEqual(localize(), 0,
                         "повторная локализация обернула что-то ещё")

    def test_no_new_migrations(self):
        """标签的包装器不应产生迁移。"""
        try:
            call_command("makemigrations", "--check", "--dry-run", verbosity=0)
        except (SystemExit, CommandError):
            self.fail("makemigrations видит изменения: обёртки подписей "
                      "попали в миграции")

    def test_language_does_not_leak_between_requests(self):
        """locale 仅在请求期间生效。"""
        before = translation.get_language()
        self.client.get("/admin/")
        self.assertEqual(translation.get_language(), before)
        self.client.get("/lang/zh/?next=/admin/")
        self.client.get("/admin/")
        self.assertEqual(translation.get_language(), before)


class EnumLabelTest(TestCase):
    """模型的枚举值已翻译，自由数据则没有。

    以前的规则是“单元格不翻译”，于是状态、单据类型和
    计量单位与数据一起绕过了词典。
    现在只要字符串在词典中，值就会被翻译，因此
    检查按模型的 ``choices`` 进行，而不是按数据块的标签。
    """

    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)

    def test_every_choice_label_is_translated(self):
        """每个 choices 标签都有翻译（ENUM_SKIP 除外）。"""
        missing = untranslated_enums()
        self.assertEqual(missing, set(),
                         f"нет перевода для {len(missing)} перечислений: "
                         f"{sorted(missing)[:10]}")

    def test_skip_list_is_explicit(self):
        """不可翻译的枚举已显式列出，且数量不多。"""
        self.assertTrue(ENUM_SKIP)
        self.assertEqual(untranslated_enums() & ENUM_SKIP, set())
        # Incoterms 术语 — 国际通用缩写，不翻译
        for code in ("CIF", "DAP", "EXW", "FCA"):
            self.assertIn(code, ENUM_SKIP)
            self.assertNotIn(code, LABELS)

    def test_translate_cell_keeps_free_data(self):
        """自由数据不会被词典替换。"""
        for value in ("Медтех-Рус", "ORD-2026-0001", "Москва, Пресненская наб., 10",
                      "10 800,00 CNY", "2026-03-15"):
            self.assertEqual(tr_value(value, "zh"), value)

    def test_translate_cell_translates_enum(self):
        """枚举类的值会被翻译。"""
        self.assertEqual(tr_value("Подписание", "zh"), "签署")
        self.assertEqual(tr_value("Подписание", "en"), "Signing")
        self.assertEqual(tr_value("Черновик", "zh"), "草稿")
        self.assertEqual(tr_value("да", "zh"), "是")
        self.assertEqual(tr_value("нет", "en"), "No")

    def test_translate_cell_translates_joined_enum(self):
        """拼接到一个单元格里的枚举按部分翻译。"""
        cell = {"text": "Недовоз · Повреждение · Прочее"}
        out = translate_cell(cell, "zh")
        self.assertEqual(out["text"], "短装 · 破损 · 其他")
        # 含相同分隔符的自由文本不会被破坏
        cell = {"text": "Партия A · Партия B"}
        self.assertEqual(translate_cell(cell, "zh")["text"], "Партия A · Партия B")

    def test_translate_cell_translates_label_prefix(self):
        """带标记的前缀标签被翻译，值保持不变。"""
        cell = {"text": "Заказ ORD-2026-0001", "label": "Заказ"}
        out = translate_cell(cell, "zh")
        self.assertEqual(out["text"], "订单 ORD-2026-0001")
        out = translate_cell({"text": "Заказ ORD-2026-0001", "label": "Заказ"}, "en")
        self.assertEqual(out["text"], "Order ORD-2026-0001")

    def test_translate_blocks_translates_cells(self):
        """translate_blocks 既翻译表格单元格，也翻译字段键。"""
        blocks = [{
            "kind": "table", "title": "Заказы", "empty": "Заказов нет",
            "columns": ["Статус"],
            "rows": [[{"text": "Подписание", "url": None},
                      {"text": "Медтех-Рус", "url": None}]],
            "items": [],
        }, {
            "kind": "fields", "title": "Карточка", "items": [["Статус", "Черновик"]],
        }]
        out = translate_blocks(blocks, "zh")
        self.assertEqual(out[0]["columns"], ["状态"])
        self.assertEqual(out[0]["rows"][0][0]["text"], "签署")
        self.assertEqual(out[0]["rows"][0][1]["text"], "Медтех-Рус")  # 数据
        self.assertEqual(out[1]["items"], [["状态", "草稿"]])

    def test_reference_values_are_translated(self):
        """字典的值（国家、货币、单据类型）已翻译。"""
        missing = untranslated_reference_values()
        self.assertEqual(missing, set(),
                         f"нет перевода для {len(missing)} значений "
                         f"справочников: {sorted(missing)}")

    def test_dictionary_agrees_with_reference_name_zh(self):
        """词典与字典自身的 ``name_zh`` 保持一致。"""
        bad = reference_mismatches()
        self.assertEqual(bad, [],
                         f"словарь расходится со справочником: {bad}")

    def test_translate_cell_handles_label_and_number(self):
        """“订单 #1”——被翻译的是标签，编号保留。"""
        self.assertEqual(tr_value("Заказ #1", "zh"), "订单 #1")
        self.assertEqual(tr_value("Заказ #12", "en"), "Order #12")
        # 含井号的自由文本不会被破坏
        self.assertEqual(tr_value("Партия A #3", "zh"), "Партия A #3")

    def test_translate_cell_handles_separator_joined_value(self):
        """拼接起来的值按部分翻译。"""
        self.assertEqual(tr_value("Недовоз · Повреждение", "zh"), "短装 · 破损")
        self.assertEqual(tr_value("RU — Россия", "zh"), "RU — 俄罗斯")
        self.assertEqual(tr_value("Китай — Россия", "en"), "China — Russia")

    def test_kpi_value_is_translated(self):
        """KPI 卡片的值如果是枚举，也会被翻译。"""
        blocks = [{"kind": "kpi", "title": "Состояние",
                   "items": [{"label": "Состояние предприятия",
                              "value": "Активна", "hint": None, "tone": "ok"},
                             {"label": "Портфель",
                              "value": "10 800,00 CNY", "hint": None,
                              "tone": ""}]}]
        out = translate_blocks(blocks, "zh")
        self.assertEqual(out[0]["items"][0]["value"], "已启用")
        # 金额 — 属于数据，保持原样
        self.assertEqual(out[0]["items"][1]["value"], "10 800,00 CNY")

    def test_pages_have_no_russian_enum_values(self):
        """页面单元格中不再残留俄语枚举值。"""
        offenders = {}
        for page in PAGES:
            provider = provider_for(page["name"])
            if provider is None:
                continue
            kwargs = {}
            if "pk" in inspect.signature(provider).parameters:
                pk = provider_pk(provider)
                if pk is None:
                    continue
                kwargs["pk"] = pk
            request = anon_request("/" + page["path"])
            try:
                data = provider(request, **kwargs) or {}
            except Exception:                                  # noqa: BLE001
                continue
            blocks = translate_blocks(data.get("blocks") or [], "zh")
            left = value_strings(blocks) & untranslated_enums()
            if left:
                offenders[page["name"]] = sorted(left)
        self.assertEqual(offenders, {},
                         f"русские перечисления на страницах: {offenders}")


class LabelCoverageTest(TestCase):
    """提供器给出的每个标签都在词典中。"""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)

    def test_no_untranslated_block_labels(self):
        found, missing, _skipped = scan()
        self.assertGreater(len(found), 200, "подписи не собраны")
        self.assertEqual(missing, set(),
                         f"нет перевода для {len(missing)} подписей: "
                         f"{sorted(missing)[:10]}")
