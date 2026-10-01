# -*- coding: utf-8 -*-
"""应用页面测试：视图与模型的连接（阶段 4）。

检查内容：
* 提供器注册表与页面注册表的一致性；
* 每个已连接页面在演示数据下的渲染；
* 标记中包含来自模型的数据而非占位；
* 带 pk 参数页面的行为（找到的对象与缺失的对象）；
* 无提供器的页面保留原型。
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
    """数据提供器与页面注册表不应出现不一致。"""

    def test_every_provider_is_a_known_page(self):
        unknown = set(PAGE_DATA) - {p["name"] for p in PAGES}
        self.assertEqual(unknown, set(), f"провайдеры без страницы: {unknown}")

    def test_coverage_matches_prototype_pages(self):
        wired, proto = coverage()
        self.assertEqual(len(wired) + len(proto), len(PAGES))
        self.assertEqual(set(proto), PROTOTYPE_PAGES)

    def test_pages_with_pk_have_provider(self):
        """带 pk 参数的页面必须连接到模型。"""
        for page in PAGES:
            if page["params"] and page["name"] not in PROTOTYPE_PAGES:
                self.assertIn(page["name"], PAGE_DATA,
                              f"{page['name']} имеет pk, но не подключена")


class WiredPagesTest(TestCase):
    """每个已连接的页面都给出来自模型的数据。"""

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
        """“login” 已接入认证并渲染表单，而非样稿。"""
        for name in ["about", "help", "register"]:
            resp = self.client.get(url_of(name))
            self.assertEqual(resp.status_code, 200, name)
            self.assertIn("Область макета", resp.content.decode())
        resp = self.client.get(url_of("login"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('name="password"', resp.content.decode())
        self.assertNotIn("Область макета", resp.content.decode())

    def test_wired_page_has_no_placeholder(self):
        resp = self.client.get(url_of("goods_list"))
        self.assertNotIn("Область макета", resp.content.decode())
        self.assertIn("Данные моделей", resp.content.decode())


class DataContentTest(TestCase):
    """标记中是来自数据库的真实值，而不是样稿。"""

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
    """带 pk 的页面：找到对象时 200，缺失时 404。"""

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
    """侧边面板的滚动位置在跳转之间保持不变。

        TradeHub 面板和后台的分区面板独立于页面滚动
        （``overflow: auto``），而浏览器只恢复窗口本身的滚动位置。
        因此跳转后面板会回滚到第一项，
        所需模块只能重新查找。

        逻辑本身位于 ``static/js/keep-scroll.js``，由独立的
        测试台验证：``tools/keep_scroll_harness.js``（按
        浏览器规则解析 + 基于 DOM 占位的逻辑）和 ``tools/browser_probe.js``
        （通过 CDP 驱动的真实 headless Chrome）。这里检查的是接入情况：
        文件由静态资源提供，脚本挂接在两个面板上，且标记中
        有它可依附的目标。
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
        """否则浏览器会得到 404，面板根本无法工作。"""
        from django.contrib.staticfiles import finders
        self.assertIsNotNone(finders.find("js/keep-scroll.js"))

    def test_portal_sidebar_is_marked_and_script_loaded(self):
        html = self.client.get("/orders/").content.decode()
        self.assertIn('data-keep-scroll="sidebar"', html)
        self.assertIn("js/keep-scroll.js", html)

    def test_script_is_deferred(self):
        """defer——为了让标记在执行时已准备就绪。"""
        html = self.client.get("/orders/").content.decode()
        self.assertRegex(
            html, r"<script[^>]+js/keep-scroll\.js[^>]*\bdefer\b")

    def test_admin_nav_sidebar_gets_the_script(self):
        """后台面板没有 data 属性——脚本按 id 查找它。"""
        self.client.force_login(self.root)
        html = self.client.get("/admin/portal/order/").content.decode()
        self.assertIn('id="nav-sidebar"', html)
        self.assertIn("js/keep-scroll.js", html)

    def test_admin_and_portal_use_different_panels(self):
        """两个面板互不重叠：TradeHub 有自己的标记。"""
        self.client.force_login(self.root)
        admin = self.client.get("/admin/portal/order/").content.decode()
        portal = self.client.get("/orders/").content.decode()
        self.assertNotIn('data-keep-scroll="sidebar"', admin)
        self.assertIn('data-keep-scroll="sidebar"', portal)


class LoginViewTest(TestCase):
    """登录页面：表单、身份认证以及返回原始页面。"""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)

    def setUp(self):
        self.client = Client(HTTP_HOST="localhost")

    def test_form_is_rendered(self):
        html = self.client.get(url_of("login")).content.decode()
        self.assertIn('name="username"', html)
        self.assertIn('name="password"', html)
        self.assertIn("ivanov", html)  # 演示账号的提示

    def test_wrong_password_shows_error_and_does_not_log_in(self):
        resp = self.client.post(url_of("login"),
                                {"username": "ivanov", "password": "wrong"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("form-error", resp.content.decode())
        self.assertFalse(resp.wsgi_request.user.is_authenticated)

    def test_successful_login_redirects_to_dashboard(self):
        resp = self.client.post(url_of("login"),
                                {"username": "ivanov",
                                 "password": "Waxx2003"})
        self.assertRedirects(resp, "/dashboard/")
        self.assertTrue(resp.wsgi_request.user.is_authenticated)

    def test_next_parameter_is_honoured(self):
        resp = self.client.post(url_of("login") + "?next=/orders/",
                                {"username": "wang",
                                 "password": "Waxx2003"})
        self.assertRedirects(resp, "/orders/")

    def test_foreign_next_is_rejected(self):
        """不允许向外部站点进行开放重定向。"""
        resp = self.client.post(
            url_of("login") + "?next=https://evil.example/",
            {"username": "ivanov", "password": "Waxx2003"})
        self.assertRedirects(resp, "/dashboard/")

    def test_authenticated_user_is_redirected_away(self):
        """已登录的用户不会看到表单。"""
        self.client.login(username="ivanov", password="Waxx2003")
        resp = self.client.get(url_of("login"))
        self.assertRedirects(resp, "/dashboard/")

    def test_selected_language_survives_login(self):
        """登录会重建会话；语言选择必须得以保留。"""
        session = self.client.session
        session["lang"] = "zh"
        session.save()
        self.client.post(url_of("login"),
                         {"username": "ivanov",
                          "password": "Waxx2003"})
        resp = self.client.get("/")
        self.assertEqual(resp.context["LANG"], "zh")
