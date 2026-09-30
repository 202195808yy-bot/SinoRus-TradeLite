# -*- coding: utf-8 -*-
"""Тесты страниц приложения: подключение представлений к моделям (этап 4).

Проверяются:
* согласованность реестра провайдеров с реестром страниц;
* отрисовка каждой подключённой страницы на демонстрационных данных;
* наличие в разметке данных из моделей, а не заглушки;
* поведение страниц с параметром pk (найденный и отсутствующий объект);
* сохранение прототипов для страниц без провайдера.
"""
from django.core.management import call_command
from django.test import Client, TestCase

from . import models as m
from .datasets import PAGE_DATA, coverage
from .pages import PAGE_BY_NAME, PAGES

PROTOTYPE_PAGES = {"about", "help", "login", "register", "logout",
                   "admin_index"}


def url_of(name, pk=None):
    path = PAGE_BY_NAME[name]["path"]
    return "/" + (path.replace("<int:pk>", str(pk)) if pk else path)


class RegistryConsistencyTest(TestCase):
    """Провайдеры данных и реестр страниц не должны расходиться."""

    def test_every_provider_is_a_known_page(self):
        unknown = set(PAGE_DATA) - {p["name"] for p in PAGES}
        self.assertEqual(unknown, set(), f"провайдеры без страницы: {unknown}")

    def test_coverage_matches_prototype_pages(self):
        wired, proto = coverage()
        self.assertEqual(len(wired) + len(proto), len(PAGES))
        self.assertEqual(set(proto), PROTOTYPE_PAGES)

    def test_pages_with_pk_have_provider(self):
        """Страницы с параметром pk обязаны быть подключены к моделям."""
        for page in PAGES:
            if page["params"] and page["name"] not in PROTOTYPE_PAGES:
                self.assertIn(page["name"], PAGE_DATA,
                              f"{page['name']} имеет pk, но не подключена")


class WiredPagesTest(TestCase):
    """Каждая подключённая страница отдаёт данные из моделей."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)

    def setUp(self):
        self.client = Client(HTTP_HOST="localhost")

    def test_all_wired_pages_render_with_data(self):
        failures = []
        for name in PAGE_DATA:
            page = PAGE_BY_NAME[name]
            pk = 1 if page["params"] else None
            resp = self.client.get(url_of(name, pk))
            if resp.status_code != 200:
                failures.append(f"{name}: {resp.status_code}")
                continue
            html = resp.content.decode()
            if "stat-row" not in html and 'class="table"' not in html:
                failures.append(f"{name}: нет блоков данных")
        self.assertEqual(failures, [], "; ".join(failures))

    def test_prototype_pages_still_render(self):
        for name in ["about", "help", "login", "register"]:
            resp = self.client.get(url_of(name))
            self.assertEqual(resp.status_code, 200, name)
            self.assertIn("Область макета", resp.content.decode())

    def test_wired_page_has_no_placeholder(self):
        resp = self.client.get(url_of("goods_list"))
        self.assertNotIn("Область макета", resp.content.decode())
        self.assertIn("Данные моделей", resp.content.decode())


class DataContentTest(TestCase):
    """В разметке — реальные значения из базы, а не макет."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)

    def setUp(self):
        self.client = Client(HTTP_HOST="localhost")

    def test_goods_list_shows_seeded_good(self):
        good = m.Good.objects.first()
        html = self.client.get(url_of("goods_list")).content.decode()
        self.assertIn(good.sku, html)
        self.assertIn(good.name_ru, html)

    def test_order_list_shows_seeded_order(self):
        order = m.Order.objects.first()
        html = self.client.get(url_of("order_list")).content.decode()
        self.assertIn(order.number, html)
        self.assertIn(order.buyer.name_ru, html)

    def test_order_detail_shows_lines_and_milestones(self):
        order = m.Order.objects.first()
        html = self.client.get(url_of("order_detail", order.pk)).content.decode()
        self.assertIn(order.number, html)
        line = order.lines.first()
        if line:
            self.assertIn(line.good.name_ru, html)
        milestone = order.milestones.first()
        if milestone:
            self.assertIn(milestone.get_kind_display(), html)

    def test_enterprise_profile_shows_demo_enterprise(self):
        ent = m.Enterprise.objects.first()
        html = self.client.get(url_of("enterprise_profile")).content.decode()
        self.assertIn(ent.name_ru, html)

    def test_dashboard_kpi_matches_database(self):
        expected = m.Order.objects.filter(
            status__in=["confirmed", "in_production"]).count()
        html = self.client.get(url_of("dashboard")).content.decode()
        self.assertIn(f">{expected}<", html)

    def test_task_board_shows_task(self):
        task = m.Task.objects.first()
        html = self.client.get(url_of("task_board")).content.decode()
        self.assertIn(task.title, html)

    def test_message_detail_shows_messages(self):
        dialog = m.Dialog.objects.first()
        html = self.client.get(url_of("message_detail", dialog.pk)).content.decode()
        self.assertIn(dialog.get_subject_kind_display(), html)
        msg = dialog.messages.first()
        if msg:
            self.assertIn(msg.body[:24], html)

    def test_statement_detail_shows_lines(self):
        statement = m.Statement.objects.first()
        html = self.client.get(url_of("statement_detail",
                                      statement.pk)).content.decode()
        self.assertIn(statement.number, html)
        line = statement.lines.first()
        if line:
            self.assertIn(line.description, html)

    def test_certificates_page_shows_expiry(self):
        cert = m.Certificate.objects.first()
        html = self.client.get(url_of("certificates_list")).content.decode()
        self.assertIn(cert.number, html)
        self.assertIn(str(cert.days_to_expiry), html)


class DetailPageParamTest(TestCase):
    """Страницы с pk: найденный объект — 200, отсутствующий — 404."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)

    def setUp(self):
        self.client = Client(HTTP_HOST="localhost")

    def test_missing_object_returns_404(self):
        for name in ["goods_detail", "rfq_detail", "quote_detail",
                     "order_detail", "shipment_detail", "message_detail",
                     "task_detail", "statement_detail"]:
            resp = self.client.get(url_of(name, 999999))
            self.assertEqual(resp.status_code, 404, name)

    def test_milestones_and_changes_of_order(self):
        order = m.Order.objects.first()
        for name in ["order_milestones", "order_changes"]:
            resp = self.client.get(url_of(name, order.pk))
            self.assertEqual(resp.status_code, 200, name)
            self.assertIn(order.number, resp.content.decode())


class SidebarScrollTest(TestCase):
    """Прокрутка боковой панели сохраняется между переходами.

    Панель TradeHub и панель разделов админки прокручиваются отдельно от
    страницы (``overflow: auto``), а браузер восстанавливает прокрутку
    только у окна. Поэтому после перехода панель откатывалась к первому
    пункту, и нужный модуль приходилось искать заново.

    Сама логика живёт в ``static/js/keep-scroll.js`` и проверяется
    отдельными стендами: ``tools/keep_scroll_harness.js`` (разбор по
    правилам браузера + логика на заглушках DOM) и ``tools/browser_probe.js``
    (настоящий headless Chrome через CDP). Здесь проверяется подключение:
    файл отдаётся статикой, скрипт подключён на обеих панелях и разметка
    даёт ему за что зацепиться.
    """

    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth import get_user_model
        call_command("seed_demo", verbosity=0)
        cls.root = get_user_model().objects.create_superuser(
            username="scroll-root", email="scroll@example.com",
            password="scroll-test-pass")

    def setUp(self):
        self.client = Client(HTTP_HOST="localhost")

    def test_script_file_is_served(self):
        """Иначе в браузере был бы 404 и панель просто не заработала бы."""
        from django.contrib.staticfiles import finders
        self.assertIsNotNone(finders.find("js/keep-scroll.js"))

    def test_portal_sidebar_is_marked_and_script_loaded(self):
        html = self.client.get("/orders/").content.decode()
        self.assertIn('data-keep-scroll="sidebar"', html)
        self.assertIn("js/keep-scroll.js", html)

    def test_script_is_deferred(self):
        """defer — чтобы разметка была готова к моменту выполнения."""
        html = self.client.get("/orders/").content.decode()
        self.assertRegex(
            html, r"<script[^>]+js/keep-scroll\.js[^>]*\bdefer\b")

    def test_admin_nav_sidebar_gets_the_script(self):
        """У панели админки нет data-атрибута — скрипт ищет её по id."""
        self.client.force_login(self.root)
        html = self.client.get("/admin/portal/order/").content.decode()
        self.assertIn('id="nav-sidebar"', html)
        self.assertIn("js/keep-scroll.js", html)

    def test_admin_and_portal_use_different_panels(self):
        """Панели не пересекаются: у TradeHub есть свой маркер."""
        self.client.force_login(self.root)
        admin = self.client.get("/admin/portal/order/").content.decode()
        portal = self.client.get("/orders/").content.decode()
        self.assertNotIn('data-keep-scroll="sidebar"', admin)
        self.assertIn('data-keep-scroll="sidebar"', portal)
