# -*- coding: utf-8 -*-
"""界面语言切换（阶段 4，后续完善）。

机制是自有的，不使用 gettext：翻译的唯一来源
是项目数据，而非 ``.po``/``.mo`` 文件。

* ``UI``     —— 界面外壳文本（导航、按钮、小节
               标题、字段标签），以 slug 为键；
* ``LABELS`` —— 数据区块的标签（表格标题、列名、KPI
               标签、字段键），见 ``core/labels.py``。键是
               提供器 ``<app>/datasets.py`` 传入的
               俄语字符串——这样字典就不会与代码脱节。

页面与模块名称取自注册表 ``core/pages.py``
（那里已有 ``ru``/``zh``/``en``），通过辅助函数 ``title_of()`` 和
``module_name()`` 获取。

**管理面板**的标签（应用、模型和字段的名称）
单独存放——``core/admin_labels.py`` + ``core/admin_i18n.py``：
它们来自 ORM 元数据，因此被包装成惰性翻译。

语言的确定顺序：参数 ``?lang=`` → 会话 → ``DEFAULT_LANG``。
由 ``core.middleware.LanguageMiddleware`` 处理。
"""

from django.utils import translation

from .labels import LABELS

LANGS = ("ru", "zh", "en")
DEFAULT_LANG = "ru"

#: 页眉切换器所用的语言名称。
LANG_LABELS = {
    "ru": "Русский",
    "zh": "中文",
    "en": "English",
}

#: 切换器按钮的短标签。
LANG_SHORT = {"ru": "RU", "zh": "中文", "en": "EN"}

#: ``<html>`` 标签 ``lang`` 属性的取值。
LANG_HTML = {"ru": "ru", "zh": "zh-Hans", "en": "en"}

#: Django 区域设置代码——用于管理面板，其翻译
#: 包含在 Django 发布包中。用同一选择也能切换面板语言。
LANG_DJANGO = {"ru": "ru", "zh": "zh-hans", "en": "en"}


def normalize(code):
    """把请求中的语言代码归一化为 ``LANGS`` 之一（或 None）。"""
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


def active_lang():
    """当前执行线程中激活的语言。

    把 Django 的区域设置代码（``zh-hans``）反向转换为应用代码
    （``zh``）。管理面板的惰性标签
    （``core/admin_i18n.py``）需要它：它们在输出时翻译，此时
    区域设置已被 middleware 激活。

    请求之外（``manage.py``、迁移、测试）区域设置等于
    ``LANGUAGE_CODE`` = ``ru-ru``——即标签的原始语言，
    因此惰性包装返回的正是它所包装的那一行字符串。
    """
    return normalize(translation.get_language()) or DEFAULT_LANG


def tr(text, lang):
    """翻译数据区块标签。未知字符串原样返回。"""
    if not text or lang == DEFAULT_LANG:
        return text
    pair = LABELS.get(text)
    if pair is None:
        return text
    return pair[0] if lang == "zh" else pair[1]


def label(text):
    """当前激活语言的标签——用于模型的 ``__str__``。

    普通标签由视图翻译（``translate_blocks``），但
    ``__str__`` 不经过这条路径：面板会在
    列表、面包屑、标题和下拉列表中显示对象。因此
    在 ``__str__`` 中硬编码的标签就地取自字典。
    """
    return tr(text, active_lang())


def t(key, lang):
    """按 slug 键取界面外壳文本。"""
    row = UI.get(key)
    if row is None:
        return key
    return row[0] if lang == "ru" else (row[1] if lang == "zh" else row[2])


def ui(lang):
    """供模板使用的界面外壳文本字典：``{{ ui.about }}``。"""
    return {key: t(key, lang) for key in UI}


#: 提供器将多个值拼入同一单元格所用的分隔符：
#: “短少 · 破损 · 其他”、“RU — 俄罗斯”
LIST_SEPS = (" · ", " — ")

#: “标签 + 编号”分隔符：“订单 #1”
CODE_SEP = " #"

#: “值 + 代码”分隔符：“件 (pcs)”、“千克 (kg)”。
#: 计量单位字典就是这样打印的。
PAREN_SEP = " ("


def tr_value(text, lang):
    """翻译单元格的值——但仅当它存在于字典中时。

    “数据 / 界面”的边界不按“单元格还是
    标签”划分，而按“字符串是否在字典中”划分：

    * ``LABELS`` 中存放标签、**枚举**（状态、单证
      种类、计量单位、角色、类别、“是”/“否”）和
      **字典值**（国家、货币、单证类型）；
    * 自由数据——企业名称、单证编号、
      地址、日期、金额——不进入字典。

    因此翻译值是安全的：未知字符串会
    原样返回。以前的规则更粗糙（“单元格不翻译”），导致
    中文界面里残留俄语的状态和单证
    种类——它们属于界面而非数据。

    另外识别三种复合情形：“订单 #1”（标签
    加编号）、“件 (pcs)”（值加括号里的代码），以及用分隔符
    （``LIST_SEPS``）拼接的值——“短少 · 破损”、
    “RU — 俄罗斯”：每一部分单独翻译。
    """
    if not text or lang == DEFAULT_LANG or not isinstance(text, str):
        return text
    pair = LABELS.get(text)
    if pair is not None:
        return pair[0] if lang == "zh" else pair[1]
    # “订单 #1”——枚举加编号：只翻译头部
    head, sep, tail = text.partition(CODE_SEP)
    if sep and head in LABELS:
        return tr(head, lang) + sep + tail
    # “件 (pcs)”——值加括号里的代码
    head, sep, tail = text.partition(PAREN_SEP)
    if sep and head in LABELS:
        return tr(head, lang) + sep + tail
    # 复合值：“短少 · 破损”、“RU — 俄罗斯”
    for splitter in LIST_SEPS:
        if splitter in text:
            parts = text.split(splitter)
            if any(part in LABELS for part in parts):
                return splitter.join(tr_value(part, lang) for part in parts)
    return text


def translate_cell(cell, lang):
    """翻译表格单元格。

    普通单元格是字典 ``{"text": …}``。如果提供器用 ``label`` 键
    标记了单元格（例如“订单 ORD-1”——标签加编号），
    则只翻译前缀标签，值保持不变。
    """
    if not isinstance(cell, dict):
        return tr_value(cell, lang)
    label = cell.get("label")
    text = cell.get("text")
    if label and isinstance(text, str):
        head = tr(label, lang)
        if head != label and text.startswith(label):
            cell["text"] = head + text[len(label):]
            return cell
    if text:
        cell["text"] = tr_value(text, lang)
    return cell


def translate_blocks(blocks, lang):
    """翻译数据区块：标签与枚举。

    单元格的值只有在字符串存在于
    字典中时才翻译（见 ``tr_value``）——自由数据保持原样。
    """
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
                # KPI 磁贴的值也可能是枚举
                # （例如“活跃”——企业的状态）
                if item.get("value") not in (None, ""):
                    item["value"] = tr_value(item["value"], lang)
                if item.get("text") and block.get("kind") == "list":
                    item["text"] = tr_value(item["text"], lang)
            elif isinstance(item, (list, tuple)) and item:
                item[0] = tr(item[0], lang)          # “字段—值”区块的键
                if len(item) > 1:
                    item[1] = tr_value(item[1], lang)  # 枚举值
        for row in block.get("rows") or []:
            for cell in row:
                translate_cell(cell, lang)
    return blocks


def label_strings(blocks):
    """收集各区块中“标签类”字符串（即需要翻译的那些）。

    供字典自检使用——``core/langcheck.py``。
    表格单元格的值不进入该集合：它们是数据，而非标签。
    例外是用 ``label`` 键标记的单元格：它们翻译的
    正是前缀标签（“订单 ORD-1”），因此标签会被检查。

    枚举（状态、单证种类、计量单位）来自模型的
    ``choices``，单独检查——``langcheck.enum_labels()``：
    它们作为值而非标签进入单元格。
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
        for row in block.get("rows") or []:
            for cell in row:
                if isinstance(cell, dict) and cell.get("label"):
                    out.add(cell["label"])
    return out


def value_strings(blocks):
    """收集各区块单元格的值——枚举翻译的候选对象。

    只有字符串存在于字典中时值才会翻译（见 ``tr_value``），
    因此自检取该集合与模型 ``choices`` 标签的
    交集——``core/langcheck.py``。
    """
    out = set()
    for block in blocks or []:
        for row in block.get("rows") or []:
            for cell in row:
                if isinstance(cell, dict):
                    if cell.get("text"):
                        out.add(str(cell["text"]))
                else:
                    out.add(str(cell))
        for item in block.get("items") or []:
            if isinstance(item, dict):
                if item.get("value") not in (None, ""):
                    out.add(str(item["value"]))
            elif isinstance(item, (list, tuple)) and len(item) > 1:
                out.add(str(item[1]))
    return out


def switch_urls(request):
    """当前页面的语言切换地址。

    指向单独的路由 ``core:set_language``，并返回
    当前地址。地址本身就带 ``?lang=`` 参数的做法不适合：
    在管理面板中 Django 会把未知参数当作列表筛选条件，
    并增加一次多余的重定向。同时应用地址中的 ``?lang=``
    仍然受支持（见 middleware）——这对 ``/?lang=zh`` 这类
    链接很方便。
    """
    from urllib.parse import quote

    from django.urls import reverse

    params = request.GET.copy()
    params.pop("lang", None)                 # 不携带上次的选择
    query = params.urlencode()
    current = request.path + ("?" + query if query else "")
    out = {}
    for code in LANGS:
        out[code] = "%s?next=%s" % (
            reverse("core:set_language", kwargs={"code": code}),
            quote(current, safe=""))
    return out


# ----------------------------------------------------------------------
# 界面外壳文本：  键 -> (俄语, 中文, 英语)
# ----------------------------------------------------------------------
UI = {
    # --- 页眉与页脚 ---
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

    # --- 页面卡片 ---
    "badge_proto": ("Прототип", "原型", "Prototype"),
    "badge_data": ("Данные моделей", "模型数据", "Model data"),
    "placeholder_title": ("Область макета", "布局区域", "Layout area"),
    "placeholder_text": (
        "Страница ещё не подключена к моделям: проверены маршрут, шаблон и "
        "передача контекста. Данные появятся после подключения провайдера "
        "в <app>/datasets.py.",
        "该页面尚未接入模型：已校验路由、模板与上下文传递。"
        "在 <app>/datasets.py 中接入数据提供器后即显示数据。",
        "This page is not yet connected to models: route, template and "
        "context passing are verified. Data appears once a provider is "
        "connected in <app>/datasets.py.",
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

    # --- 主页 ---
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

    # --- 面板 ---
    "module_links": ("Переходы к модулям", "模块入口", "Module links"),
    "pages_short": ("стр.", "页", "pp."),

    # --- 数据区块 ---
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

    # --- 登录页面 ---
    "login_username": ("Имя пользователя", "用户名", "Username"),
    "login_password": ("Пароль", "密码", "Password"),
    "login_error": (
        "Неверное имя пользователя или пароль.",
        "用户名或密码不正确。",
        "Invalid username or password.",
    ),
    "login_hint_title": (
        "Демонстрационные учётные записи",
        "演示账号",
        "Demo accounts",
    ),
    "login_hint_password": (
        "Пароль у всех демонстрационных учётных записей:",
        "所有演示账号的密码：",
        "Password for all demo accounts:",
    ),
    "login_role_admin": (
        "Администратор платформы", "平台管理员", "Platform administrator"),
    "login_role_buyer": (
        "Снабжение · российское предприятие",
        "采购 · 俄方企业",
        "Procurement · Russian company",
    ),
    "login_role_supplier": (
        "Поставщик · китайское предприятие",
        "供应商 · 中方企业",
        "Supplier · Chinese company",
    ),
    "login_role_carrier": (
        "Оператор перевозчика", "承运方操作员", "Carrier operator"),
}
