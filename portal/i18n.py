# -*- coding: utf-8 -*-
"""Переключение языка интерфейса (этап 4, доработка).

Механизм собственный, без gettext: единственным источником переводов
служат данные проекта, а не файлы ``.po``/``.mo``.

* ``UI``     — тексты оболочки интерфейса (навигация, кнопки, заголовки
               разделов, подписи полей) по ключам-слагам;
* ``LABELS`` — подписи блоков данных (заголовки таблиц, колонки, подписи
               KPI, ключи полей), см. ``portal/labels.py``. Ключом служит
               русская строка, которую передаёт провайдер
               ``portal/datasets.py``, — так словарь не разъезжается с кодом.

Названия страниц и модулей берутся из реестра ``portal/pages.py``
(там уже есть ``ru``/``zh``/``en``) через хелперы ``title_of()`` и
``module_name()``.

Язык определяется так: параметр ``?lang=`` → сессия → ``DEFAULT_LANG``.
Обрабатывается ``portal.middleware.LanguageMiddleware``.
"""

from .labels import LABELS

LANGS = ("ru", "zh", "en")
DEFAULT_LANG = "ru"

#: Названия языков для переключателя в шапке.
LANG_LABELS = {
    "ru": "Русский",
    "zh": "中文",
    "en": "English",
}

#: Короткие подписи для кнопок переключателя.
LANG_SHORT = {"ru": "RU", "zh": "中文", "en": "EN"}

#: Значения атрибута ``lang`` тега ``<html>``.
LANG_HTML = {"ru": "ru", "zh": "zh-Hans", "en": "en"}

#: Коды локалей Django — для административной панели, переводы которой
#: входят в поставку Django. Позволяют переключать и её тем же выбором.
LANG_DJANGO = {"ru": "ru", "zh": "zh-hans", "en": "en"}


def normalize(code):
    """Приводит код языка из запроса к одному из ``LANGS`` (или None)."""
    if not code:
        return None
    code = str(code).strip().lower().replace("_", "-")
    if code in ("ru", "ru-ru", "russian", "рус"):
        return "ru"
    if code in ("zh", "zh-hans", "zh-cn", "cn", "chinese", "中文", "кит"):
        return "zh"
    if code in ("en", "en-us", "en-gb", "english", "англ"):
        return "en"
    return None


def tr(text, lang):
    """Переводит подпись блока данных. Неизвестные строки возвращает как есть."""
    if not text or lang == DEFAULT_LANG:
        return text
    pair = LABELS.get(text)
    if pair is None:
        return text
    return pair[0] if lang == "zh" else pair[1]


def t(key, lang):
    """Текст оболочки по ключу-слагу."""
    row = UI.get(key)
    if row is None:
        return key
    return row[0] if lang == "ru" else (row[1] if lang == "zh" else row[2])


def ui(lang):
    """Словарь текстов оболочки для шаблонов: ``{{ ui.about }}``."""
    return {key: t(key, lang) for key in UI}


def translate_blocks(blocks, lang):
    """Переводит подписи в блоках данных (значения ячеек не трогает)."""
    if lang == DEFAULT_LANG or not blocks:
        return blocks
    for block in blocks:
        if block.get("title"):
            block["title"] = tr(block["title"], lang)
        if block.get("empty"):
            block["empty"] = tr(block["empty"], lang)
        if block.get("note"):
            block["note"] = tr(block["note"], lang)
        if block.get("columns"):
            block["columns"] = [tr(col, lang) for col in block["columns"]]
        for item in block.get("items") or []:
            if isinstance(item, dict):
                if item.get("label"):
                    item["label"] = tr(item["label"], lang)
                if item.get("hint"):
                    item["hint"] = tr(item["hint"], lang)
            elif isinstance(item, (list, tuple)) and item:
                item[0] = tr(item[0], lang)          # ключ блока «поле — значение»
    return blocks


def label_strings(blocks):
    """Собирает «подписные» строки блоков (те, что подлежат переводу).

    Используется самопроверкой словаря — ``portal/langcheck.py``.
    Значения ячеек таблиц в набор не попадают: это данные, а не подписи.
    """
    out = set()
    for block in blocks or []:
        for key in ("title", "empty", "note"):
            if block.get(key):
                out.add(block[key])
        for col in block.get("columns") or []:
            out.add(str(col))
        for item in block.get("items") or []:
            if isinstance(item, dict):
                if item.get("label"):
                    out.add(item["label"])
                if item.get("hint"):
                    out.add(item["hint"])
            elif isinstance(item, (list, tuple)) and item:
                out.add(str(item[0]))
    return out


def switch_urls(request):
    """Адреса переключения языка для текущей страницы.

    Ведёт на отдельный маршрут ``portal:set_language`` с возвратом на
    текущий адрес. Параметр ``?lang=`` в самом адресе для этого не годится:
    в административной панели Django считает неизвестный параметр фильтром
    списка и добавляет лишнее перенаправление. При этом ``?lang=`` в
    адресах приложения по-прежнему поддерживается (см. middleware) — это
    удобно для ссылок вида ``/?lang=zh``.
    """
    from urllib.parse import quote

    from django.urls import reverse

    params = request.GET.copy()
    params.pop("lang", None)                 # не тащим прошлый выбор
    query = params.urlencode()
    current = request.path + ("?" + query if query else "")
    out = {}
    for code in LANGS:
        out[code] = "%s?next=%s" % (
            reverse("portal:set_language", kwargs={"code": code}),
            quote(current, safe=""))
    return out


# ----------------------------------------------------------------------
# Тексты оболочки интерфейса:  ключ -> (русский, китайский, английский)
# ----------------------------------------------------------------------
UI = {
    # --- шапка и подвал ---
    "brand_sub": (
        "Платформа совместной работы · Россия — Китай",
        "中俄跨境贸易协同平台",
        "Collaboration platform · Russia — China",
    ),
    "nav_about": ("О платформе", "关于平台", "About"),
    "nav_help": ("Справка", "帮助", "Help"),
    "nav_dashboard": ("Панель", "看板", "Dashboard"),
    "nav_login": ("Вход", "登录", "Sign in"),
    "nav_logout": ("Выход", "退出", "Sign out"),
    "sidebar_title": ("Структура приложения", "应用结构", "Application structure"),
    "crumb_home": ("Главная", "首页", "Home"),
    "lang_label": ("Язык", "语言", "Language"),
    "footer_line1": (
        "Курсовой проект · дисциплина «Разработка веб-приложений на Python» · "
        "Владимирский государственный университет, 2026 г.",
        "课程设计 · 学科《Python Web 应用开发》 · "
        "弗拉基米尔国立大学，2026 年",
        "Course project · subject “Web application development in Python” · "
        "Vladimir State University, 2026",
    ),
    "footer_line2": (
        "Прототип интерфейса: маршрутизация и шаблонизация. Бизнес-логика "
        "и модели данных реализуются на последующих этапах.",
        "界面原型：路由与模板化。业务逻辑与数据模型在后续阶段实现。",
        "Interface prototype: routing and templating. Business logic and "
        "data models are implemented in later stages.",
    ),

    # --- карточка страницы ---
    "badge_proto": ("Прототип", "原型", "Prototype"),
    "badge_data": ("Данные моделей", "模型数据", "Model data"),
    "placeholder_title": ("Область макета", "布局区域", "Layout area"),
    "placeholder_text": (
        "Страница ещё не подключена к моделям: проверены маршрут, шаблон и "
        "передача контекста. Данные появятся после подключения провайдера "
        "в portal/datasets.py.",
        "该页面尚未接入模型：已校验路由、模板与上下文传递。"
        "在 portal/datasets.py 中接入数据提供器后即显示数据。",
        "This page is not yet connected to models: route, template and "
        "context passing are verified. Data appears once a provider is "
        "connected in portal/datasets.py.",
    ),
    "sec_purpose": ("Назначение страницы", "页面用途", "Page purpose"),
    "sec_content": ("Основное содержание", "主要内容", "Main content"),
    "sec_route": ("Сведения о маршруте", "路由信息", "Route details"),
    "f_page_url": ("Адрес страницы", "页面地址", "Page address"),
    "f_route_name": ("Имя маршрута", "路由名", "Route name"),
    "f_view": ("Представление", "视图", "View"),
    "f_access": ("Режим доступа", "访问方式", "Access mode"),
    "f_params": ("Параметры маршрута", "路由参数", "Route parameters"),
    "access_public": ("Общедоступная", "公开", "Public"),
    "access_auth": ("Требуется вход", "需登录", "Sign-in required"),
    "access_role": ("Ограничено ролью", "按角色限制", "Role-restricted"),

    # --- главная страница ---
    "index_kicker": ("Курсовой проект · веб-приложение",
                     "课程设计 · Web 应用", "Course project · web application"),
    "hero_title": (
        "Легковесная платформа совместной работы<br>"
        "для трансграничной торговли России и Китая",
        "中俄跨境贸易<br>轻量级协同平台",
        "A lightweight collaboration platform<br>"
        "for Russia–China cross-border trade",
    ),
    "hero_lead": (
        "Платформа занимает позицию «слой торговой кооперации»: она не "
        "заменяет функции брокера, перевозчика или банка, а сводит "
        "разрозненные сведения и задачи нескольких сторон на одну "
        "временную шкалу сделки.",
        "平台定位于「贸易协同层」：不替代报关行、承运人或银行，"
        "而是把多方的分散信息与任务汇聚到同一条交易时间轴上。",
        "The platform positions itself as a “trade cooperation layer”: it "
        "does not replace the broker, carrier or bank, but brings the "
        "scattered records and tasks of several parties onto a single "
        "deal timeline.",
    ),
    "btn_login": ("Войти в систему", "登录系统", "Sign in"),
    "btn_register": ("Зарегистрироваться", "注册", "Register"),
    "btn_about": ("О платформе", "关于平台", "About"),
    "feat_title": ("Ключевые возможности", "核心能力", "Key capabilities"),
    "feat1_h": ("Исполнение сделки", "交易执行", "Deal execution"),
    "feat1_p": (
        "Заказы, партии, этапы перевозки и регистрация инцидентов в пути — "
        "на одной временной шкале с указанием ответственного.",
        "订单、批次、运输阶段与在途异常登记——同一条时间轴，标明责任人。",
        "Orders, shipments, transport milestones and in-transit "
        "exceptions — on one timeline with an owner.",
    ),
    "feat2_h": ("Документы и соответствие", "单证与合规",
                "Documents and compliance"),
    "feat2_p": (
        "Реестр документов, контроль комплектности, сроки действия "
        "сертификатов с напоминаниями за 60, 30 и 7 дней.",
        "单证登记、完整性控制、证书有效期，并在 60/30/7 天前提醒。",
        "Document register, completeness control, certificate validity "
        "with reminders 60, 30 and 7 days ahead.",
    ),
    "feat3_h": ("Двуязычное общение", "双语沟通", "Bilingual communication"),
    "feat3_p": (
        "Диалоги привязаны к бизнес-объекту; шаблоны сообщений и "
        "терминология поддерживают русский и китайский языки.",
        "会话绑定到业务对象；消息模板与术语支持俄语和中文。",
        "Conversations are bound to a business object; message templates "
        "and terminology support Russian and Chinese.",
    ),
    "feat4_h": ("Аналитика и задачи", "分析与任务", "Analytics and tasks"),
    "feat4_p": (
        "Сводные показатели исполнения, сроки и затраты по каналам, "
        "доска задач с эскалацией по истечении срока.",
        "执行汇总指标、按渠道的工期与成本、带逾期升级的任务看板。",
        "Summary execution metrics, lead time and cost by channel, a task "
        "board with overdue escalation.",
    ),
    "app_structure": ("Структура приложения", "应用结构",
                      "Application structure"),
    "app_structure_lead": (
        "Приложение разделено на двенадцать модулей. Ниже приведены модули "
        "и количество страниц в каждом из них.",
        "应用划分为十二个模块。下表列出各模块及其页面数量。",
        "The application is divided into twelve modules. The table below "
        "lists the modules and the number of pages in each.",
    ),
    "th_module": ("Модуль", "模块", "Module"),
    "th_name": ("Название", "名称", "Name"),
    "th_name_zh": ("Китайское название", "中文名称", "Chinese name"),
    "th_pages": ("Страниц", "页面数", "Pages"),

    # --- панель ---
    "module_links": ("Переходы к модулям", "模块入口", "Module links"),
    "pages_short": ("стр.", "页", "pp."),

    # --- блоки данных ---
    "demo_notice": (
        "Демонстрационный режим: показаны данные первого предприятия базы. "
        "Ограничение доступа по ролям — этап 5 «Пользователи приложения».",
        "演示模式：显示数据库中第一个企业的数据。"
        "按角色的访问限制属于阶段 5《应用用户》。",
        "Demo mode: the data of the first company in the database is shown. "
        "Role-based access restriction is stage 5, “Application users”.",
    ),
    "truncated_note": (
        "Показаны первые {n} записей из общего числа.",
        "仅显示前 {n} 条记录。",
        "Showing the first {n} records.",
    ),
}
