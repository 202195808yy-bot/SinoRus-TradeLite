# -*- coding: utf-8 -*-
"""Тесты переключения языка интерфейса (доработка этапа 4).

Проверяются:

* выбор языка: ``?lang=`` / маршрут ``/lang/<код>/`` -> сессия ->
  язык по умолчанию;
* перевод названий и описаний страниц из реестра ``portal/pages.py``;
* перевод подписей блоков данных (заголовки таблиц, подписи KPI);
* полнота словарей ``portal/labels.py`` и ``portal/i18n.py``;
* переключение административной панели тем же выбором языка;
* языковая чистота: русская версия без иероглифов, китайская — без
  кириллицы (кроме общепринятых обозначений).
"""

import re
from urllib.parse import quote

from django.core.management import call_command
from django.test import Client, TestCase

from .i18n import (DEFAULT_LANG, LABELS, LANGS, LANG_LABELS, LANG_SHORT, UI,
                   normalize, tr, translate_blocks)
from .langcheck import scan
from .pages import PAGES, content_of, module_name, purpose_of, title_of
from .views import _page_data

CJK = re.compile(r"[\u4e00-\u9fff]")
CYR = re.compile(r"[\u0400-\u04ff]")

#: кириллица, допустимая в китайских текстах (общепринятые обозначения)
CYR_ALLOWED_IN_ZH = {"ИНН"}


def cyr_words(text):
    """Слова из кириллицы в строке."""
    return set(re.findall(r"[\u0400-\u04ff][\u0400-\u04ff\-.]*", text))


class LanguageSelectionTest(TestCase):
    """Выбор языка: параметр запроса, сессия, значение по умолчанию."""

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
        # следующий запрос без параметра — язык берётся из сессии
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
        # переключатель ведёт на отдельный маршрут и сохраняет текущий адрес
        self.assertIn("/lang/ru/?next=%2Forders%2F", html)
        self.assertIn("/lang/en/?next=%2Forders%2F", html)

    def test_switch_endpoint_remembers_and_returns(self):
        """Маршрут переключения запоминает язык и возвращает на исходный адрес."""
        response = self.client.get("/lang/en/?next=" + quote("/orders/", safe=""))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/orders/")
        self.assertEqual(self.client.session["lang"], "en")
        self.assertEqual(self.client.get("/orders/").context["LANG"], "en")

    def test_switch_endpoint_rejects_external_redirect(self):
        """Защита от открытого перенаправления: чужой адрес заменяется на «/»."""
        for bad in ("//evil.example.com/", "https://evil.example.com/", "evil"):
            response = self.client.get(
                "/lang/ru/?next=" + quote(bad, safe=""))
            self.assertEqual(response["Location"], "/", bad)

    def test_switch_endpoint_ignores_unknown_code(self):
        """Неизвестный код языка не ломает выбор: остаётся прежний."""
        self.client.get("/lang/zh/?next=%2Forders%2F")
        self.client.get("/lang/de/?next=%2Forders%2F")
        self.assertEqual(self.client.session["lang"], "zh")

    def test_html_lang_attribute_follows_choice(self):
        self.assertIn('lang="ru"', self.client.get("/").content.decode())
        self.assertIn('lang="zh-Hans"',
                      self.client.get("/?lang=zh").content.decode())
        self.assertIn('lang="en"', self.client.get("/?lang=en").content.decode())


class PageContentLanguageTest(TestCase):
    """Название, назначение и содержание страницы — на текущем языке."""

    def test_resolved_fields_match_registry_helpers(self):
        for page in PAGES:
            for lang in LANGS:
                data = _page_data(page, lang)
                self.assertEqual(data["title"], title_of(page, lang))
                self.assertEqual(data["purpose"], purpose_of(page, lang))
                self.assertEqual(data["content"], content_of(page, lang))

    def test_russian_version_has_no_cjk(self):
        """Русская версия описаний не должна содержать иероглифов."""
        offenders = [(p["name"], field)
                     for p in PAGES
                     for field in ("ru", "purpose_ru", "content_ru")
                     if CJK.search(p[field])]
        self.assertEqual(offenders, [], f"китайские символы в ru: {offenders}")

    def test_chinese_version_is_translated_and_clean(self):
        """Китайская версия переведена и почти не содержит кириллицы."""
        for page in PAGES:
            data = _page_data(page, "zh")
            self.assertTrue(CJK.search(data["purpose"]),
                            f"{page['name']}: назначение не переведено")
            extra = cyr_words(data["purpose"]) | cyr_words(data["content"])
            self.assertTrue(extra <= CYR_ALLOWED_IN_ZH,
                            f"{page['name']}: кириллица в китайской версии "
                            f"{extra - CYR_ALLOWED_IN_ZH}")

    def test_legacy_keys_are_overridden_by_language(self):
        """Исторические ключи purpose/content больше не «залипают» на китайском."""
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
    """Подписи блоков данных переводятся, значения ячеек — нет."""

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
        # русская версия без иероглифов, китайская — без кириллицы
        self.assertFalse(any(CJK.search(h) for h in ru))
        self.assertFalse(any(CYR.search(h) for h in zh))

    def test_block_titles_are_translated(self):
        html = self.client.get("/orders/1/?lang=zh").content.decode()
        for expected in ("订单卡片", "订单明细", "执行阶段"):
            self.assertIn(expected, html)

    def test_cell_values_are_not_translated(self):
        """Значения ячеек — данные, они не подменяются словарём."""
        response = self.client.get("/orders/?lang=zh")
        html = response.content.decode()
        self.assertIn("ORD-", html)          # номера документов как есть

    def test_translate_blocks_keeps_values(self):
        blocks = [{"kind": "table", "title": "Заказы", "empty": "Заказов нет",
                   "columns": ["Статус"],
                   "rows": [[{"text": "Подписан", "url": None}]],
                   "items": []}]
        out = translate_blocks(blocks, "zh")
        self.assertEqual(out[0]["title"], "订单")
        self.assertEqual(out[0]["columns"], ["状态"])
        self.assertEqual(out[0]["empty"], "无订单")
        self.assertEqual(out[0]["rows"][0][0]["text"], "Подписан")

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
    """Словари переводов интерфейса заполнены полностью."""

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
    """Административная панель переключается тем же выбором языка.

    Панель использует шаблоны и переводы Django, поэтому здесь проверяется,
    что ``LanguageMiddleware`` активирует нужную локаль и что переключатель
    языка отрисован.

    Переключатель ведёт на маршрут ``portal:set_language``, а не на
    ``?lang=``: в списках панели Django считает неизвестный параметр
    фильтром и отвечает лишним перенаправлением (см.
    ``test_admin_list_page_rejects_lang_query``).
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
        """Переключение языка так же, как это делает ссылка в шапке панели."""
        return self.client.get(
            "/lang/%s/?next=%s" % (code, quote(target, safe="")))

    def test_admin_index_renders(self):
        self.assertEqual(self.client.get("/admin/").status_code, 200)

    def test_admin_follows_language(self):
        """Интерфейс панели переводится вместе с выбором языка."""
        # Django переводит «Add» как Добавить / 增加 / Add
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
        """Ссылка из шапки действительно переключает язык и возвращает назад."""
        html = self.client.get("/admin/").content.decode()
        match = re.search(r'href="(/lang/zh/\?next=[^"]+)"', html)
        self.assertIsNotNone(match, "ссылка переключателя не найдена")
        response = self.client.get(match.group(1).replace("&amp;", "&"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/admin/")
        self.assertEqual(self.client.session["lang"], "zh")

    def test_admin_switcher_on_login_page(self):
        """На странице входа переключатель тоже есть (блок branding)."""
        client = Client(HTTP_HOST="localhost")       # анонимный
        html = client.get("/admin/login/").content.decode()
        self.assertIn("admin-lang", html)
        self.assertIn("/lang/ru/?next=%2Fadmin%2Flogin%2F", html)

    def test_admin_language_is_remembered(self):
        self.switch("en")
        self.assertEqual(self.client.session["lang"], "en")
        self.assertEqual(self.client.get("/admin/").context["LANG"], "en")

    def test_admin_deep_pages_keep_working(self):
        """Выбранный язык не мешает разделам панели (адрес без ?lang=)."""
        self.switch("zh")
        for url in ("/admin/portal/order/", "/admin/portal/order/1/change/",
                    "/admin/portal/good/", "/admin/auth/user/"):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)

    def test_admin_list_page_rejects_lang_query(self):
        """``?lang=`` в списке панели Django принимает за фильтр.

        Это и есть причина отдельного маршрута переключения: запрос
        ``/admin/portal/order/?lang=zh`` отвечает перенаправлением с
        пометкой об ошибке (``?e=1``), а не страницей списка.
        """
        response = self.client.get("/admin/portal/order/?lang=zh")
        self.assertEqual(response.status_code, 302)
        self.assertIn("e=1", response["Location"])

    def test_portal_and_admin_share_the_choice(self):
        """Один и тот же выбор языка действует и в приложении, и в панели."""
        self.client.get("/?lang=zh")
        self.assertEqual(self.client.get("/admin/").context["LANG"], "zh")
        self.assertEqual(self.client.get("/orders/").context["LANG"], "zh")


class LabelCoverageTest(TestCase):
    """Каждая подпись, которую отдают провайдеры, есть в словаре."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)

    def test_no_untranslated_block_labels(self):
        found, missing, _skipped = scan()
        self.assertGreater(len(found), 200, "подписи не собраны")
        self.assertEqual(missing, set(),
                         f"нет перевода для {len(missing)} подписей: "
                         f"{sorted(missing)[:10]}")
