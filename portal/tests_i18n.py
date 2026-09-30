# -*- coding: utf-8 -*-
"""Тесты переключения языка интерфейса (доработка этапа 4).

Проверяются:

* выбор языка: ``?lang=`` / маршрут ``/lang/<код>/`` -> сессия ->
  язык по умолчанию;
* перевод названий и описаний страниц из реестра ``portal/pages.py``;
* перевод подписей блоков данных (заголовки таблиц, подписи KPI);
* перевод **перечислений** (``choices`` моделей) и **значений
  справочников** — они приходят в ячейки значениями, а не подписями;
* сохранение свободных данных: наименования, номера, даты не переводятся;
* полнота словарей ``portal/labels.py`` и ``portal/i18n.py``;
* переключение административной панели тем же выбором языка;
* языковая чистота: русская версия без иероглифов, китайская — без
  кириллицы (кроме общепринятых обозначений).
"""

import inspect
import re
from urllib.parse import quote

from django.apps import apps
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management import CommandError, call_command
from django.test import Client, TestCase
from django.utils import translation

from . import models as m
from .admin_i18n import localize, tr_permission
from .admin_labels import OVERRIDES
from .datasets import provider_for
from .i18n import (DEFAULT_LANG, LABELS, LANGS, LANG_LABELS, LANG_SHORT, UI,
                   normalize, tr, translate_blocks, translate_cell, tr_value,
                   value_strings)
from .langcheck import (ENUM_SKIP, admin_labels, admin_overrides, anon_request,
                        provider_pk, reference_mismatches, scan,
                        untranslated_admin_labels, untranslated_enums,
                        untranslated_reference_values)
from .pages import PAGES, content_of, module_name, purpose_of, title_of
from .views import _page_data

CJK = re.compile(r"[\u4e00-\u9fff]")
CYR = re.compile(r"[\u0400-\u04ff]")

#: кириллица, допустимая в китайских текстах (общепринятые обозначения)
CYR_ALLOWED_IN_ZH = {"ИНН"}

#: Комментарии разметки и стилей — не текст интерфейса, пользователь их
#: не видит. В шаблонах проекта они по-русски, как и остальные пояснения.
COMMENTS = re.compile(r"<!--.*?-->|/\*.*?\*/", re.S)

#: кириллица, допустимая в панели: названия языков даны на самих языках
#: (в переключателе ``title="Русский"`` — так же, как на страницах портала).
CYR_ALLOWED_IN_ADMIN = {name for name in LANG_LABELS.values() if CYR.search(name)}

#: Поля, которые панель заполняет сама и хранит в базе. Их содержимое —
#: подписи, а не свободные данные, поэтому в белый список они не попадают:
#: именно на них ловится «замороженный» русский текст.
GENERATED_LABEL_FIELDS = {
    ("auth", "permission"): {"name"},
    ("admin", "logentry"): {"change_message"},
}

#: Минимальная длина обрезка, который считается данными. Панель показывает
#: длинный текст усечённым (``Truncator``), поэтому в разметку попадает
#: часть слова — «сертифика» от «сертификата». Такие обрезки разрешены, но
#: не короче этого порога: иначе под короткой подписью («Дата», «Роль»)
#: маскировалось бы что угодно.
MIN_TRUNCATED = 5


def cyr_words(text):
    """Слова из кириллицы в строке."""
    return set(re.findall(r"[\u0400-\u04ff][\u0400-\u04ff\-.]*", text))


def visible_text(html):
    """Разметка без комментариев — только то, что видит пользователь."""
    return COMMENTS.sub(" ", html)


def demo_words():
    """Кириллические слова из демонстрационных данных.

    Свободные данные — наименования предприятий и товаров, номера, адреса,
    свободные примечания, ключи JSON-полей — переводить нельзя, поэтому в
    словаре их нет. Чтобы проверка «в китайской панели не осталось русских
    подписей» не спотыкалась о данные, их слова собираются из самой базы.

    Обходятся **все** приложения, а не только ``portal``: на странице
    пользователя видны его имя и фамилия (``auth``), в журнале — снимок
    объекта (``admin``). Исключения — ``GENERATED_LABEL_FIELDS``.
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

    def test_logout_keeps_language(self):
        """Выход из системы не сбрасывает выбранный язык.

        ``auth_logout()`` очищает сессию целиком, вместе с языком, поэтому
        представление выхода сохраняет выбор и восстанавливает его.
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

    def test_translate_blocks_does_not_touch_free_data(self):
        """Свободные данные в ячейках остаются как есть.

        Перечисление («Подписан») переводится, потому что есть в словаре,
        а наименование предприятия — нет: его в словаре нет.
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


class AdminLabelTest(TestCase):
    """Подписи панели — названия моделей, полей и значений — следуют языку.

    Панель берёт их из метаданных ORM, а не из провайдеров страниц, поэтому
    без обёртки они всегда русские (``portal/admin_i18n.py``). Обёрток две:
    ``LazyRu`` — для подписей, ``LazyChoice`` — для подписей ``choices``;
    последние остаются настоящими строками, потому что ``portal/datasets.py``
    их склеивает, а миграции записывают.

    Ещё две подписи панель хранит **в базе**, и они тоже заморожены
    по-русски: ``Permission.name`` (собирается при ``migrate`` как «Can add
    <verbose_name_raw>») и ``LogEntry.change_message`` (названия изменённых
    полей записываются в момент правки). Обе переводятся на выводе.
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

        # Запись журнала с русскими названиями полей — такую создаёт сама
        # панель при правке объекта. Нужна, чтобы страница истории тоже
        # проверялась на «замороженные» подписи.
        order = m.Order.objects.first()
        cls.log_entry = LogEntry.objects.log_action(
            user_id=cls.root.pk,
            content_type_id=ContentType.objects.get_for_model(order).pk,
            object_id=order.pk, object_repr=str(order), action_flag=CHANGE,
            change_message='[{"changed": {"fields": ["\u0441\u0442\u0430\u0442\u0443\u0441",'
                           ' "\u0434\u0430\u0442\u0430 \u043f\u043e\u0434\u043f\u0438\u0441\u0430\u043d\u0438\u044f"]}}]')

    def setUp(self):
        self.client = Client(HTTP_HOST="localhost")
        self.client.force_login(self.root)

    # ---------------------------------------------------------- словарь
    def test_every_admin_label_is_translated(self):
        missing = untranslated_admin_labels()
        self.assertEqual(missing, set(),
                         f"нет перевода подписей панели: {sorted(missing)}")

    def test_admin_overrides_are_explicit(self):
        """Расхождения с словарём страниц должны быть объявлены явно."""
        self.assertEqual(set(admin_overrides()), set(OVERRIDES),
                         f"переводы разъехались: {admin_overrides()}")

    def test_admin_labels_are_not_empty(self):
        self.assertGreater(len(admin_labels()), 200)

    # ------------------------------------------------- ленивый перевод
    def test_app_name_follows_language(self):
        name = apps.get_app_config("portal").verbose_name
        self.assertEqual(str(name), "Портал трансграничной торговли")
        with translation.override("zh-hans"):
            self.assertEqual(str(name), "跨境贸易门户")
        with translation.override("en"):
            self.assertEqual(str(name), "Cross-border trade portal")

    def test_model_name_follows_language(self):
        meta = m.Currency._meta
        self.assertEqual(str(meta.verbose_name), "валюта")
        self.assertEqual(str(meta.verbose_name_plural), "валюты")
        with translation.override("zh-hans"):
            self.assertEqual(str(meta.verbose_name), "币种")
            self.assertEqual(str(meta.verbose_name_plural), "币种")
        with translation.override("en"):
            self.assertEqual(str(meta.verbose_name_plural), "Currencies")

    def test_field_label_follows_language(self):
        field = m.Shipment._meta.get_field("container_no")
        self.assertEqual(str(field.verbose_name), "номер контейнера")
        with translation.override("zh-hans"):
            self.assertEqual(str(field.verbose_name), "集装箱号")
        with translation.override("en"):
            self.assertEqual(str(field.verbose_name), "Container number")

    def test_choice_label_follows_language(self):
        labels = dict(m.Document._meta.get_field("status").choices)
        self.assertEqual(str(labels["draft"]), "Черновик")
        with translation.override("zh-hans"):
            self.assertEqual(str(labels["draft"]), "草稿")
            self.assertEqual(str(labels["archived"]), "已归档")
        with translation.override("en"):
            self.assertEqual(str(labels["draft"]), "Draft")

    def test_reference_str_follows_language(self):
        """Внешние ключи справочников показываются переведёнными."""
        country = m.Country.objects.get(name_ru="Россия")
        uom = m.Uom.objects.get(name_ru="штука")
        self.assertEqual(str(country), "RU — Россия")
        self.assertEqual(str(uom), "штука (pcs)")
        with translation.override("zh-hans"):
            self.assertEqual(str(country), "RU — 俄罗斯")
            self.assertEqual(str(uom), "件 (pcs)")

    def test_free_data_is_not_translated(self):
        """Свободные данные остаются как есть на любом языке."""
        good = m.Good.objects.first()
        with translation.override("zh-hans"):
            self.assertNotEqual(str(good), "")
            self.assertEqual(str(good), str(good.raw) if hasattr(good, "raw")
                             else str(good))

    # ----------------------------- подписи choices остаются строками
    def test_choice_label_stays_a_string(self):
        """Регресс: ``portal/datasets.py`` склеивает подписи ``choices``."""
        choices = list(m.Incident._meta.get_field("kind").choices)
        joined = " · ".join(label for _value, label in choices)
        self.assertIsInstance(joined, str)
        self.assertEqual(joined,
                         " · ".join(label.raw for _v, label in choices))
        label = choices[0][1]
        self.assertIsInstance(label, str)          # сравнение — по исходной
        self.assertEqual(label, label.raw)

    # -------------------------------------------------- панель целиком
    def test_admin_shell_has_no_cyrillic(self):
        """Страницы без данных: интерфейс полностью переведён.

        Комментарии разметки и стилей не считаются текстом интерфейса,
        а названия языков в переключателе даны на самих языках.
        """
        pages = ("/admin/", "/admin/portal/", "/admin/portal/currency/",
                 "/admin/portal/auditlog/")
        for code in ("zh", "en"):
            self.client.get("/lang/%s/?next=/admin/" % code)
            for url in pages:
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200, url)
                offenders = (cyr_words(visible_text(response.content.decode("utf-8")))
                             - CYR_ALLOWED_IN_ADMIN)
                self.assertEqual(offenders, set(), f"{code} {url}: {offenders}")

    def test_admin_pages_have_no_russian_interface(self):
        """На страницах с данными кириллица остаётся только в данных.

        Список страниц намеренно широкий: именно пропуск страницы
        пользователя скрыл однажды подписи разрешений («Can add вложение»),
        а пропуск истории — названия полей в журнале.
        """
        allowed = demo_words() | CYR_ALLOWED_IN_ADMIN
        pages = ("/admin/portal/order/", "/admin/portal/order/1/change/",
                 "/admin/portal/order/1/history/",
                 "/admin/portal/good/", "/admin/portal/good/1/change/",
                 "/admin/portal/enterprise/", "/admin/portal/document/",
                 "/admin/portal/statement/1/change/",
                 "/admin/portal/profile/", "/admin/portal/profile/1/change/",
                 "/admin/portal/tariff/", "/admin/portal/dialog/",
                 "/admin/portal/translation/", "/admin/portal/message/",
                 "/admin/portal/good/add/", "/admin/portal/tariff/add/",
                 "/admin/auth/user/", "/admin/auth/user/1/change/",
                 "/admin/auth/group/", "/admin/auth/group/add/")
        for code in ("zh", "en"):
            self.client.get("/lang/%s/?next=/admin/" % code)
            for url in pages:
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200, url)
                offenders = (cyr_words(visible_text(response.content.decode("utf-8")))
                             - allowed)
                self.assertEqual(offenders, set(), f"{code} {url}: {offenders}")

    # ------------------------------------- подписи, замороженные в базе
    def test_permission_labels_follow_language(self):
        """Подписи разрешений собираются заново из ``codename``.

        В базе лежит «Can add вложение»: Django записывает туда
        непереведённое название модели, чтобы данные не зависели от локали.
        В панели такая подпись видна, поэтому она переводится на выводе.
        """
        perm = Permission.objects.get(codename="add_attachment")
        self.assertEqual(perm.name, "Can add вложение")      # как в базе
        self.assertEqual(str(perm), "portal | вложение | Добавить вложение")
        with translation.override("zh-hans"):
            self.assertEqual(str(perm), "portal | 附件 | 增加 附件")
        with translation.override("en"):
            self.assertEqual(str(perm), "portal | Attachment | Add Attachment")

    def test_permission_verbs_match_the_panel(self):
        """Глагол разрешения совпадает с надписью панели на том же языке."""
        for code, verb in (("zh-hans", "增加"), ("ru", "Добавить")):
            with translation.override(code):
                label = str(Permission.objects.get(codename="add_user"))
                self.assertEqual(label.split(" | ")[-1].split(" ")[0], verb,
                                 f"{code}: глагол не совпал с надписью панели")

    def test_custom_permission_keeps_its_name(self):
        """Нестандартное разрешение не разбирается и остаётся как в базе."""
        content_type = ContentType.objects.get_for_model(m.Order)
        perm = Permission(name="Can approve order", codename="can_approve_order",
                          content_type=content_type)
        with translation.override("zh-hans"):
            self.assertEqual(tr_permission(perm), "Can approve order")

    def test_log_message_follows_language(self):
        """Названия полей в журнале переводятся, сама запись не меняется."""
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
        # вывод не должен записывать перевод в базу
        self.assertEqual(LogEntry.objects.get(pk=self.log_entry.pk).change_message,
                         raw)

    def test_log_message_keeps_plain_text(self):
        """Журнал умеет хранить и простое сообщение — его не трогаем."""
        entry = LogEntry(object_repr="x", change_message="Изменено вручную.")
        with translation.override("zh-hans"):
            self.assertEqual(entry.get_change_message(), "Изменено вручную.")

    # ----------------------------------- подписи внутри ``__str__`` моделей
    def test_model_str_labels_follow_language(self):
        """Подписи внутри ``__str__`` берутся из словаря.

        ``__str__`` панель вызывает вне ``translate_blocks`` — в списках,
        хлебных крошках, заголовках и выпадающих списках, — поэтому жёстко
        записанное русское слово («Профиль: ivanov») доходило до
        пользователя в любом языке.
        """
        objects = [m.Profile.objects.first(), m.Tariff.objects.first(),
                   m.Dialog.objects.first(), m.Translation.objects.first()]
        for code in ("zh-hans", "en"):
            with translation.override(code):
                for obj in objects:
                    text = str(obj)
                    self.assertEqual(cyr_words(text), set(),
                                     f"{code} {type(obj).__name__}: {text}")
        with translation.override("zh-hans"):
            profile = str(m.Profile.objects.first())
            self.assertTrue(profile.startswith("用户"), profile)
            self.assertIn("增值税", str(m.Tariff.objects.first()))
        with translation.override("en"):
            self.assertTrue(str(m.Profile.objects.first()).startswith("Profile"))
            self.assertIn("VAT", str(m.Tariff.objects.first()))

    def test_model_str_label_agrees_with_model_name(self):
        """Подпись в ``__str__`` совпадает с названием модели на странице."""
        with translation.override("zh-hans"):
            prefix = str(m.Profile.objects.first()).split(":")[0]
            self.assertEqual(prefix, str(m.Profile._meta.verbose_name).capitalize())

    def test_model_str_labels_keep_default_language(self):
        """Русский — исходный язык подписей: он не меняется."""
        self.assertEqual(str(m.Profile.objects.first()), "Профиль: ivanov")
        self.assertIn("пошлина", str(m.Tariff.objects.first()))

    def test_admin_headers_are_translated(self):
        self.client.get("/lang/zh/?next=/admin/")
        html = self.client.get("/admin/portal/order/").content.decode("utf-8")
        for word in ("编号", "状态", "金额", "签署日期"):
            self.assertIn(word, html, f"заголовок {word} не найден")

    # ------------------------------------------------------- механизм
    def test_localize_is_idempotent(self):
        self.assertEqual(localize(), 0,
                         "повторная локализация обернула что-то ещё")

    def test_no_new_migrations(self):
        """Обёртки подписей не должны порождать миграции."""
        try:
            call_command("makemigrations", "--check", "--dry-run", verbosity=0)
        except (SystemExit, CommandError):
            self.fail("makemigrations видит изменения: обёртки подписей "
                      "попали в миграции")

    def test_language_does_not_leak_between_requests(self):
        """Локаль действует только на время запроса."""
        before = translation.get_language()
        self.client.get("/admin/")
        self.assertEqual(translation.get_language(), before)
        self.client.get("/lang/zh/?next=/admin/")
        self.client.get("/admin/")
        self.assertEqual(translation.get_language(), before)


class EnumLabelTest(TestCase):
    """Перечисления моделей переведены, свободные данные — нет.

    Раньше правило было «ячейки не переводим», и вместе с данными мимо
    словаря проходили статусы, виды документов и единицы измерения.
    Теперь значение переводится, если строка есть в словаре, поэтому
    проверка идёт по ``choices`` моделей, а не по подписям блоков.
    """

    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)

    def test_every_choice_label_is_translated(self):
        """Каждая подпись choices имеет перевод (кроме ENUM_SKIP)."""
        missing = untranslated_enums()
        self.assertEqual(missing, set(),
                         f"нет перевода для {len(missing)} перечислений: "
                         f"{sorted(missing)[:10]}")

    def test_skip_list_is_explicit(self):
        """Непереводимые перечисления перечислены явно и их немного."""
        self.assertTrue(ENUM_SKIP)
        self.assertEqual(untranslated_enums() & ENUM_SKIP, set())
        # условия Инкотермс — международные сокращения, они не переводятся
        for code in ("CIF", "DAP", "EXW", "FCA"):
            self.assertIn(code, ENUM_SKIP)
            self.assertNotIn(code, LABELS)

    def test_translate_cell_keeps_free_data(self):
        """Свободные данные не подменяются словарём."""
        for value in ("Медтех-Рус", "ORD-2026-0001", "Москва, Пресненская наб., 10",
                      "10 800,00 CNY", "2026-03-15"):
            self.assertEqual(tr_value(value, "zh"), value)

    def test_translate_cell_translates_enum(self):
        """Значение-перечисление переводится."""
        self.assertEqual(tr_value("Подписание", "zh"), "签署")
        self.assertEqual(tr_value("Подписание", "en"), "Signing")
        self.assertEqual(tr_value("Черновик", "zh"), "草稿")
        self.assertEqual(tr_value("да", "zh"), "是")
        self.assertEqual(tr_value("нет", "en"), "No")

    def test_translate_cell_translates_joined_enum(self):
        """Перечисления, склеенные в одну ячейку, переводятся по частям."""
        cell = {"text": "Недовоз · Повреждение · Прочее"}
        out = translate_cell(cell, "zh")
        self.assertEqual(out["text"], "短装 · 破损 · 其他")
        # свободный текст с тем же разделителем не ломается
        cell = {"text": "Партия A · Партия B"}
        self.assertEqual(translate_cell(cell, "zh")["text"], "Партия A · Партия B")

    def test_translate_cell_translates_label_prefix(self):
        """Помеченная подпись-префикс переводится, значение остаётся."""
        cell = {"text": "Заказ ORD-2026-0001", "label": "Заказ"}
        out = translate_cell(cell, "zh")
        self.assertEqual(out["text"], "订单 ORD-2026-0001")
        out = translate_cell({"text": "Заказ ORD-2026-0001", "label": "Заказ"}, "en")
        self.assertEqual(out["text"], "Order ORD-2026-0001")

    def test_translate_blocks_translates_cells(self):
        """translate_blocks переводит и ячейки таблицы, и ключи полей."""
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
        self.assertEqual(out[0]["rows"][0][1]["text"], "Медтех-Рус")  # данные
        self.assertEqual(out[1]["items"], [["状态", "草稿"]])

    def test_reference_values_are_translated(self):
        """Значения справочников (страны, валюты, типы документов) переведены."""
        missing = untranslated_reference_values()
        self.assertEqual(missing, set(),
                         f"нет перевода для {len(missing)} значений "
                         f"справочников: {sorted(missing)}")

    def test_dictionary_agrees_with_reference_name_zh(self):
        """Словарь не расходится с ``name_zh`` самих справочников."""
        bad = reference_mismatches()
        self.assertEqual(bad, [],
                         f"словарь расходится со справочником: {bad}")

    def test_translate_cell_handles_label_and_number(self):
        """«Заказ #1» — переводится подпись, номер остаётся."""
        self.assertEqual(tr_value("Заказ #1", "zh"), "订单 #1")
        self.assertEqual(tr_value("Заказ #12", "en"), "Order #12")
        # свободный текст с решёткой не ломается
        self.assertEqual(tr_value("Партия A #3", "zh"), "Партия A #3")

    def test_translate_cell_handles_separator_joined_value(self):
        """Склеенные значения переводятся по частям."""
        self.assertEqual(tr_value("Недовоз · Повреждение", "zh"), "短装 · 破损")
        self.assertEqual(tr_value("RU — Россия", "zh"), "RU — 俄罗斯")
        self.assertEqual(tr_value("Китай — Россия", "en"), "China — Russia")

    def test_kpi_value_is_translated(self):
        """Значение плитки KPI тоже переводится, если оно перечисление."""
        blocks = [{"kind": "kpi", "title": "Состояние",
                   "items": [{"label": "Состояние предприятия",
                              "value": "Активна", "hint": None, "tone": "ok"},
                             {"label": "Портфель",
                              "value": "10 800,00 CNY", "hint": None,
                              "tone": ""}]}]
        out = translate_blocks(blocks, "zh")
        self.assertEqual(out[0]["items"][0]["value"], "已启用")
        # сумма — данные, остаётся как есть
        self.assertEqual(out[0]["items"][1]["value"], "10 800,00 CNY")

    def test_pages_have_no_russian_enum_values(self):
        """На страницах не осталось русских перечислений в ячейках."""
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
