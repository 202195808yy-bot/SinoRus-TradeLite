# -*- coding: utf-8 -*-
"""应用页面的注册表（单一数据源）。

统一注册表供三方使用：
  * 各应用的 urls.py — 构建路由（见 ``app_of()``）；
  * core/views.py    — 通用页面渲染器；
  * docs/pages.{ru,zh,en}.md 与文档《应用页面说明》 —
    页面说明。

记录字段：
    name      — 路由名（url name）；
    path      — URL 模板（不含前导斜杠）；
    view      — 视图函数名（所在模块由 ``app_of()`` 给出）；
    module    — 模块代码（M0..M11）；
    app       — 承载该页面的应用（见 ``APP_OF``）；
    ru/zh/en  — 页面的俄语、中文和英语名称；
    access    — 访问模式：public | auth | role；
    purpose_* — 页面在语言 * 下的用途；
    content_* — 页面在语言 * 下的主要内容；
    params    — 路由参数：dict {"ru":…, "zh":…, "en":…} 或 None。

取值应通过辅助函数 `title_of() / purpose_of() / content_of() /
params_of() / module_name()` 进行，而不是直接按键名访问 — 这样
新增语言时使用方无需改动。

兼容性：不带后缀的历史键（`purpose`、`content`）
保留为中文版本的别名 — 它们被模板
`templates/portal/page.html` 和文档《应用页面说明》
的生成器使用。新代码应使用辅助函数。

翻译完整性由 `tools/check_i18n.py` 自动检查。
"""

LANGS = ("ru", "zh", "en")

MODULES = [
    ("M0", "Общие страницы", "公共页面", "Common pages"),
    ("M1", "Предприятие и аккаунт", "企业与账号",
     "Enterprise and account"),
    ("M2", "Товары", "商品管理", "Goods"),
    ("M3", "Запросы и предложения", "询价与报价", "RFQs and quotes"),
    ("M4", "Заказы", "订单管理", "Orders"),
    ("M5", "Логистика и пункты пропуска", "物流与口岸",
     "Logistics and border crossings"),
    ("M6", "Документы и соответствие", "单证与合规",
     "Documents and compliance"),
    ("M7", "Двуязычное общение", "双语沟通", "Bilingual communication"),
    ("M8", "Задачи и напоминания", "任务与提醒", "Tasks and reminders"),
    ("M9", "Аналитика", "数据看板", "Analytics"),
    ("M10", "Расчёты и сверка", "结算与对账",
     "Settlements and reconciliation"),
    ("M11", "Администрирование", "系统管理", "Administration"),
]

MODULE_BY_CODE = {code: (ru, zh, en) for code, ru, zh, en in MODULES}

PAGES = [
    # ---------------------------------------------------------- M0
    dict(name="index", path="", view="index_view", module="M0",
         ru="Главная страница", zh="首页", en="Home", access="public",
         purpose_ru="Показать гостям и авторизованным пользователям "
                    "позиционирование платформы, её ключевые возможности "
                    "и сводку текущих дел.",
         purpose_zh="向未登录访客与已登录用户展示平台定位、核心能力与当前待办概览。",
         purpose_en="Presents the platform's positioning, core capabilities "
                    "and a summary of current to-dos to both anonymous "
                    "visitors and signed-in users.",
         content_ru="Позиционирование платформы одной фразой, четыре "
                    "карточки ключевых возможностей, сводка данных о "
                    "торговле России и Китая, вход и регистрация; для "
                    "авторизованных — три дополнительные карточки: задачи "
                    "на сегодня, проблемные заказы, сертификаты с "
                    "истекающим сроком.",
         content_zh="平台一句话定位、四类核心能力卡片、中俄贸易背景数据摘要、登录/注册入口；已登录时追加今日待办、异常订单、临期证书三张摘要卡。",
         content_en="A one-line positioning statement, four capability "
                    "cards, key figures on China–Russia trade and "
                    "sign-in/sign-up entry points; when signed in, three "
                    "extra summary cards for today's tasks, problematic "
                    "orders and expiring certificates.",
         params=None),
    dict(name="about", path="about/", view="about_view", module="M0",
         ru="О платформе", zh="关于平台", en="About the platform",
         access="public",
         purpose_ru="Пояснить место платформы в цепочке создания "
                    "стоимости, четыре границы её ответственности и "
                    "категории пользователей.",
         purpose_zh="说明平台所处的产业链位置、四条业务边界与服务对象。",
         purpose_en="Explains the platform's position in the value chain, "
                    "its four business boundaries and the audiences it "
                    "serves.",
         content_ru="Позиционирование платформы (слой торговой кооперации), "
                    "четыре действия, которые платформа намеренно не "
                    "выполняет (платёжные операции, таможенное "
                    "оформление, вынесение суждения о соответствии, сбор "
                    "посторонних персональных данных), три категории "
                    "пользователей.",
         content_zh="平台定位（贸易协同层）、不做的四件事（资金业务、报关代理、合规结论判定、无关个人信息采集）、三类服务对象。",
         content_en="Platform positioning (trade collaboration layer), the "
                    "four things it deliberately does not do (payment "
                    "operations, customs brokerage, deciding compliance "
                    "outcomes, collecting unrelated personal data) and the "
                    "three audiences it serves.",
         params=None),
    dict(name="help", path="help/", view="help_view", module="M0",
         ru="Справка", zh="帮助与使用指南", en="Help and user guide",
         access="public",
         purpose_ru="Дать инструкции по работе, разделённые по ролям, и "
                    "ответы на частые вопросы.",
         purpose_zh="提供按角色划分的操作指引与常见问题解答。",
         purpose_en="Provides role-specific operating instructions and "
                    "answers to frequently asked questions.",
         content_ru="Пошаговые инструкции по ролям (китайский торговый "
                    "посредник, китайский менеджер, российский партнёр, "
                    "оператор экспедитора), глоссарий, часто задаваемые "
                    "вопросы.",
         content_zh="按角色（中方贸易商、中方业务员、俄方合作方、货代操作员）分类的操作步骤、术语表、常见问题。",
         content_en="Step-by-step instructions grouped by role (Chinese "
                    "trader, Chinese sales representative, Russian partner, "
                    "freight-forwarder operator), a glossary and a FAQ.",
         params=None),
    dict(name="login", path="accounts/login/", view="login_view", module="M0",
         ru="Вход в систему", zh="登录", en="Sign in", access="public",
         purpose_ru="Проверить учётные данные пользователя и создать "
                    "сессию.",
         purpose_zh="校验用户身份并建立登录会话。",
         purpose_en="Verifies the user's identity and establishes a "
                    "signed-in session.",
         content_ru="Поля логина и пароля, запоминание входа, переключение "
                    "на вход по коду из СМС, ссылка восстановления пароля; "
                    "при ошибке — понятная причина и число оставшихся "
                    "попыток.",
         content_zh="账号与密码输入、记住登录状态、验证码登录切换、忘记密码入口；登录失败给出明确原因与剩余尝试次数。",
         content_en="Account and password fields, \"keep me signed in\", a "
                    "switch to one-time-code sign-in and a password-reset "
                    "link; failed attempts show a clear reason and the "
                    "number of attempts left.",
         params=None),
    dict(name="register", path="accounts/register/", view="register_view",
         module="M0", ru="Регистрация", zh="注册", en="Sign up",
         access="public",
         purpose_ru="Создать личную учётную запись и привязать её к "
                    "организации.",
         purpose_zh="创建个人账号并绑定所属企业主体。",
         purpose_en="Creates a personal account and links it to the company "
                    "it belongs to.",
         content_ru="Регистрация по телефону или электронной почте "
                    "(поддержка кодов Китая +86 и России +7), проверка "
                    "сложности пароля, обратный отсчёт кода "
                    "подтверждения, переход к привязке организации.",
         content_zh="手机号与邮箱注册（支持中国 +86 与俄罗斯 +7 区号）、密码强度校验、验证码倒计时、企业主体关联入口。",
         content_en="Sign-up by phone number or e-mail (supporting China's "
                    "+86 and Russia's +7 country codes), "
                    "password-strength validation, a verification-code "
                    "countdown and a link for attaching a company entity.",
         params=None),
    dict(name="logout", path="accounts/logout/", view="logout_view",
         module="M0", ru="Выход из системы", zh="退出登录", en="Sign out",
         access="auth",
         purpose_ru="Завершить текущую сессию и очистить локальное "
                    "состояние входа.",
         purpose_zh="结束当前会话并清理本地登录态。",
         purpose_en="Ends the current session and clears the local "
                    "sign-in state.",
         content_ru="Подтверждение выхода; после выхода — переход на "
                    "главную страницу.",
         content_zh="退出确认提示；退出后跳转至首页。",
         content_en="A confirmation prompt; after signing out the user is "
                    "redirected to the home page.",
         params=None),

    # ---------------------------------------------------------- M1
    dict(name="enterprise_profile", path="enterprises/profile/",
         view="enterprise_profile_view", module="M1",
         ru="Профиль предприятия", zh="企业双语档案",
         en="Company bilingual profile", access="auth",
         purpose_ru="Вести двуязычный профиль организации — источник "
                    "данных для автоматического заполнения документов и "
                    "договоров.",
         purpose_zh="维护企业主体的中俄双语档案，作为单证与合同自动填充的数据源。",
         purpose_en="Maintains the bilingual profile of the company entity, "
                    "which serves as the data source for auto-filling "
                    "documents and contracts.",
         content_ru="Название организации, код единого социального кредита "
                    "/ ИНН, юридический адрес, контакты, банковские "
                    "реквизиты; китайские и российские поля заполняются "
                    "рядом, незаполненные пункты подсвечиваются.",
         content_zh="企业名称、统一社会信用代码 / ИНН（俄罗斯纳税人识别号）、"
                    "注册地址、联系方式、银行信息；中俄双语字段并排填写，"
                    "缺失项高亮提示补录。",
         content_en="Company name, unified social credit code / INN, "
                    "registered address, contact details and bank "
                    "information; Chinese and Russian fields are filled in "
                    "side by side and missing items are highlighted for "
                    "completion.",
         params=None),
    dict(name="enterprise_verification", path="enterprises/verification/",
         view="enterprise_verification_view", module="M1",
         ru="Подтверждение субъекта", zh="主体认证", en="Entity verification",
         access="auth",
         purpose_ru="Подавать документы на подтверждение организации и "
                    "отслеживать их проверку, ограничивая возможности "
                    "неподтверждённых организаций.",
         purpose_zh="提交并跟踪企业主体认证材料，控制未认证主体的功能范围。",
         purpose_en="Submits and tracks company verification documents and "
                    "governs what unverified entities are allowed to do.",
         content_ru="Загрузка лицензии на ведение деятельности или "
                    "российского регистрационного документа, "
                    "подтверждение распознанных полей, отслеживание "
                    "статуса проверки (не подано / на проверке / принято / "
                    "отклонено), показ причины отклонения.",
         content_zh="营业执照或俄方登记文件上传、字段识别结果确认、审核状态跟踪（待提交/审核中/已通过/已驳回）、驳回原因展示。",
         content_en="Upload of a business licence or Russian registration "
                    "document, confirmation of the extracted fields, "
                    "review-status tracking (not submitted / under review / "
                    "approved / rejected) and display of the rejection "
                    "reason.",
         params=None),
    dict(name="enterprise_members", path="enterprises/members/",
         view="enterprise_members_view", module="M1",
         ru="Сотрудники и роли", zh="成员与角色管理",
         en="Members and roles", access="role",
         purpose_ru="Управлять структурой организации, учётными записями "
                    "сотрудников и распределением ролей.",
         purpose_zh="管理企业组织架构、成员账号与角色分配。",
         purpose_en="Manages the company structure, member accounts and "
                    "role assignments.",
         content_ru="Список сотрудников (имя, роль, статус, последний "
                    "вход), назначение ролей, блокировка учётной записи и "
                    "передача дел; доступно только руководителю и "
                    "администраторам.",
         content_zh="成员列表（姓名、角色、状态、最近登录）、角色分配、账号停用与交接；仅业务负责人与管理员可见。",
         content_en="Member list (name, role, status, last sign-in), role "
                    "assignment, account deactivation and handover; "
                    "visible only to the business owner and administrators.",
         params=None),
    dict(name="enterprise_invitations", path="enterprises/invitations/",
         view="enterprise_invitations_view", module="M1",
         ru="Приглашение партнёров", zh="协作者邀请",
         en="Partner invitations", access="auth",
         purpose_ru="Приглашать российских партнёров и операторов "
                    "экспедитора к совместной работе по выбранным заказам.",
         purpose_zh="邀请俄方合作方或货代操作员加入指定订单的协同范围。",
         purpose_en="Invites Russian partners or freight-forwarder operators "
                    "to join the collaboration scope of selected orders.",
         content_ru="Выбор типа приглашаемого, область совместной работы "
                    "(по заказу или по партии), срок действия, ссылка и "
                    "QR-код приглашения, отслеживание статуса приглашения.",
         content_zh="邀请对象类型选择、协同范围（按订单或按批次）、有效期设置、邀请链接与二维码、邀请状态跟踪。",
         content_en="Choice of invitee type, collaboration scope (by order "
                    "or by shipment), validity period, invitation link and "
                    "QR code, and invitation-status tracking.",
         params=None),

    # ---------------------------------------------------------- M2
    dict(name="goods_list", path="goods/", view="goods_list_view",
         module="M2", ru="Список товаров", zh="商品列表", en="Goods list",
         access="auth",
         purpose_ru="Искать карточки товаров организации по категории, "
                    "статусу и ключевому слову.",
         purpose_zh="按品类、状态与关键词检索本企业商品卡片。",
         purpose_en="Searches the company's goods records by category, "
                    "status and keyword.",
         content_ru="Список в виде карточек (изображение, двуязычное "
                    "название, краткая спецификация, отметки о "
                    "соответствии), часто используемые фильтры, "
                    "сортировка, переход к массовым операциям.",
         content_zh="卡片化列表（图片、中俄双语标题、规格摘要、合规属性标识）、常用筛选标签、排序、批量操作入口。",
         content_en="Card-based list (image, bilingual title, specification "
                    "summary, compliance flags), frequently used filter "
                    "tags, sorting and bulk-action entry points.",
         params=None),
    dict(name="goods_detail", path="goods/<int:pk>/", view="goods_detail_view",
         module="M2", ru="Карточка товара", zh="商品详情", en="Goods detail",
         access="auth",
         purpose_ru="Показать полную информацию о товаре, его свойства "
                    "соответствия и историю версий.",
         purpose_zh="展示商品完整信息、合规属性与历史版本。",
         purpose_en="Shows the complete goods record, its compliance "
                    "attributes and its version history.",
         content_ru="Двуязычное название и описание, характеристики, "
                    "сведения об упаковке, набор изображений, код ТН ВЭД и "
                    "свойства соответствия, связанные сертификаты, история "
                    "версий и сравнение различий.",
         content_zh="中俄双语标题与描述、规格参数、包装信息、图片集、HS 编码与合规属性、关联证书、版本历史与差异对比。",
         content_en="Bilingual title and description, specification "
                    "parameters, packaging information, image gallery, HS "
                    "code and compliance attributes, linked certificates, "
                    "version history and difference comparison.",
         params={"ru": "pk — идентификатор товара",
                 "zh": "pk — 商品标识",
                 "en": "pk — goods identifier"}),
    dict(name="goods_form", path="goods/new/", view="goods_form_view",
         module="M2", ru="Создание и редактирование товара", zh="新建/编辑商品",
         en="Create or edit goods", access="auth",
         purpose_ru="Вводить и изменять карточку товара с поддержкой "
                    "двуязычных полей.",
         purpose_zh="录入或修改商品卡片，支持中俄双语字段。",
         purpose_en="Creates or edits a goods record with bilingual fields.",
         content_ru="Заполнение в четыре шага — основные сведения, "
                    "характеристики, упаковка, свойства соответствия; не "
                    "более пяти полей на шаг; индикатор прогресса сверху; "
                    "черновик сохраняется автоматически.",
         content_zh="按基本信息、规格、包装、合规属性分四步填写，每步不超过 5 个字段；顶部进度指示；草稿自动保存。",
         content_en="Four steps — basic information, specifications, "
                    "packaging and compliance attributes — with no more "
                    "than five fields each; a progress indicator at the "
                    "top; drafts are saved automatically.",
         params=None),

    # ---------------------------------------------------------- M3
    dict(name="rfq_list", path="rfqs/", view="rfq_list_view", module="M3",
         ru="Список запросов", zh="询价单列表", en="RFQ list", access="auth",
         purpose_ru="Видеть в одном месте запросы, отправленные и "
                    "полученные организацией, и их статус ответа.",
         purpose_zh="集中查看本企业发出与收到的询价单及其响应状态。",
         purpose_en="Shows in one place the requests for quotation the "
                    "company has sent and received, with their response "
                    "status.",
         content_ru="Группировка «созданные мной / ожидают моего ответа / "
                    "закрытые»; в строке — товар, количество, диапазон "
                    "целевой цены, ожидаемый срок поставки и оставшееся "
                    "время на ответ.",
         content_zh="按“我发起的 / 待我响应 / 已关闭”分组；列表项展示商品、数量、目标价区间、期望交期与剩余响应时间。",
         content_en="Grouped into \"started by me / awaiting my response / "
                    "closed\"; each row shows the goods, quantity, target "
                    "price range, expected delivery date and remaining "
                    "response time.",
         params=None),
    dict(name="rfq_create", path="rfqs/new/", view="rfq_create_view",
         module="M3", ru="Создание запроса", zh="发起询价", en="Create an RFQ",
         access="auth",
         purpose_ru="Позволить российскому партнёру создать запрос с "
                    "указанием количества, целевой цены и срока поставки.",
         purpose_zh="由俄方合作方发起询价，明确数量、目标价与交期。",
         purpose_en="Lets a Russian partner raise a request for quotation "
                    "stating quantity, target price and delivery date.",
         content_ru="Выбор товара, количество, диапазон целевой цены, "
                    "ожидаемый срок поставки, место получения, примечания; "
                    "помещается на одном экране, после отправки китайская "
                    "сторона получает уведомление.",
         content_zh="商品选择、数量、目标价区间、期望交期、收货地、补充说明；一屏可填完，提交后即时通知中方。",
         content_en="Goods selection, quantity, target price range, expected "
                    "delivery date, place of delivery and free-text notes; "
                    "fits on a single screen and notifies the Chinese side "
                    "immediately on submission.",
         params=None),
    dict(name="rfq_detail", path="rfqs/<int:pk>/", view="rfq_detail_view",
         module="M3", ru="Карточка запроса", zh="询价单详情", en="RFQ detail",
         access="auth",
         purpose_ru="Показать все условия запроса и связанные предложения, "
                    "обеспечив возможность ответить напрямую.",
         purpose_zh="展示询价单全部条款与关联报价，支持直接响应。",
         purpose_en="Shows all terms of the request together with linked "
                    "quotations and allows a direct response.",
         content_ru="Условия запроса, инициатор и время, список связанных "
                    "предложений, журнал переходов статуса, переходы к "
                    "ответу и к диалогу.",
         content_zh="询价条款、发起方与时间、关联报价列表、状态流转记录、响应入口与会话入口。",
         content_en="RFQ terms, requester and timestamp, list of linked "
                    "quotations, status-transition log, and entry points "
                    "for responding and for opening a conversation.",
         params={"ru": "pk — идентификатор запроса",
                 "zh": "pk — 询价单标识",
                 "en": "pk — RFQ identifier"}),
    dict(name="quote_list", path="quotes/", view="quote_list_view",
         module="M3", ru="Список предложений", zh="报价单列表",
         en="Quotation list", access="auth",
         purpose_ru="Показать предложения, отправленные и полученные "
                    "организацией, с их версиями и сроком действия.",
         purpose_zh="查看本企业发出与收到的报价单及其版本与有效期。",
         purpose_en="Shows the quotations the company has issued and "
                    "received, with their versions and validity periods.",
         content_ru="В строке — товар, цена за единицу и валюта, условие "
                    "поставки, число дней до истечения срока, номер "
                    "версии; предложения с истекающим сроком "
                    "подсвечиваются.",
         content_zh="列表项展示商品、单价与币种、贸易术语、有效期剩余天数、版本号；临期报价高亮提示。",
         content_en="Each row shows the goods, unit price and currency, "
                    "trade term, days left before expiry and version "
                    "number; quotations nearing expiry are highlighted.",
         params=None),
    dict(name="quote_detail", path="quotes/<int:pk>/", view="quote_detail_view",
         module="M3", ru="Карточка предложения", zh="报价单详情",
         en="Quotation detail", access="auth",
         purpose_ru="Показать все условия предложения, ступенчатые цены и "
                    "историю версий, обеспечив перевод в заказ.",
         purpose_zh="展示报价全部条款、阶梯价与版本历史，支持转为订单。",
         purpose_en="Shows all quotation terms, tiered pricing and version "
                    "history, and allows conversion into an order.",
         content_ru="Цена за единицу, валюта, ступенчатые цены, срок "
                    "поставки, условие поставки, срок действия, примечания; "
                    "история версий и сравнение различий; после отправки "
                    "предложение нельзя изменить напрямую — изменения "
                    "создают новую версию.",
         content_zh="单价、币种、阶梯价、交期、贸易术语、有效期、备注；版本历史与差异对比；发出后不可直接修改，修改生成新版本。",
         content_en="Unit price, currency, tiered pricing, delivery date, "
                    "trade term, validity period and notes; version "
                    "history with difference comparison; once issued a "
                    "quotation cannot be edited directly — changes create "
                    "a new version.",
         params={"ru": "pk — идентификатор предложения",
                 "zh": "pk — 报价单标识",
                 "en": "pk — quotation identifier"}),

    # ---------------------------------------------------------- M4
    dict(name="order_list", path="orders/", view="order_list_view",
         module="M4", ru="Список заказов", zh="订单列表", en="Order list",
         access="auth",
         purpose_ru="Искать заказы по статусу, каналу и дате, быстро "
                    "находя проблемные и просроченные.",
         purpose_zh="按状态、通道与时间检索订单，快速定位异常与超期订单。",
         purpose_en="Searches orders by status, corridor and date so that "
                    "problematic and overdue orders can be found quickly.",
         content_ru="Список в виде карточек (номер заказа, контрагент, "
                    "метка текущего статуса, ключевые даты, следующее "
                    "действие), фильтр по статусу, проблемные заказы "
                    "закрепляются сверху, переход к экспорту.",
         content_zh="卡片化列表（订单号、对方企业、当前状态标签、关键时间、下一步动作）、状态筛选、异常订单置顶、导出入口。",
         content_en="Card-based list (order number, counterparty, current "
                    "status tag, key dates, next action), status filters, "
                    "problematic orders pinned to the top and an export "
                    "entry point.",
         params=None),
    dict(name="order_detail", path="orders/<int:pk>/", view="order_detail_view",
         module="M4", ru="Карточка заказа", zh="订单详情", en="Order detail",
         access="auth",
         purpose_ru="Ответить на вопросы о текущем прогрессе заказа и "
                    "следующем действии через структуру «статус — "
                    "хронология этапов — действия».",
         purpose_zh="以“状态区 + 里程碑时间轴 + 操作区”三段式结构回答订单当前进度与下一步动作。",
         purpose_en="Answers \"where is this order now and what happens "
                    "next\" through a three-part layout: status block, "
                    "milestone timeline and action block.",
         content_ru="Сверху блок статуса (текущий статус, следующее "
                    "действие, ответственная сторона); в середине "
                    "хронология этапов (узел, время, исполнитель, "
                    "миниатюры подтверждений); снизу блок действий, "
                    "который предлагает только то, что разрешено ролью и "
                    "статусом заказа.",
         content_zh="顶部状态区（当前状态、下一步动作、责任方）；中部里程碑时间轴（节点、时间、操作人、凭证缩略图）；底部操作区（按角色与状态动态给出可执行动作）。",
         content_en="Status block at the top (current status, next action, "
                    "responsible party); milestone timeline in the middle "
                    "(node, time, operator, evidence thumbnails); action "
                    "block at the bottom offering only the actions "
                    "permitted by the user's role and the order's status.",
         params={"ru": "pk — идентификатор заказа",
                 "zh": "pk — 订单标识",
                 "en": "pk — order identifier"}),
    dict(name="order_milestones", path="orders/<int:pk>/milestones/",
         view="order_milestones_view", module="M4",
         ru="Этапы исполнения заказа", zh="履约里程碑", en="Order milestones",
         access="auth",
         purpose_ru="Регистрировать и просматривать этапы исполнения "
                    "заказа в хронологическом порядке, формируя "
                    "прослеживаемую цепочку доказательств.",
         purpose_zh="按时间顺序登记与查看订单履约节点，形成可追溯的证据链。",
         purpose_en="Records and reviews fulfilment milestones in "
                    "chronological order, forming a traceable chain of "
                    "evidence.",
         content_ru="Форма регистрации этапа (тип этапа, время, исполнитель, "
                    "описание, загрузка подтверждений), полное отображение "
                    "хронологии, просмотр и скачивание подтверждений.",
         content_zh="节点登记表单（节点类型、时间、操作人、说明、凭证上传）、时间轴全量展示、凭证查看与下载。",
         content_en="Milestone entry form (node type, time, operator, "
                    "description, evidence upload), a full timeline view, "
                    "and viewing and downloading of evidence.",
         params={"ru": "pk — идентификатор заказа",
                 "zh": "pk — 订单标识",
                 "en": "pk — order identifier"}),
    dict(name="order_changes", path="orders/<int:pk>/changes/",
         view="order_changes_view", module="M4",
         ru="Изменения заказа", zh="订单变更单", en="Order change notes",
         access="auth",
         purpose_ru="Фиксировать изменения количества, цены, срока и "
                    "условий получения в виде листа изменений, сохраняя "
                    "прежние значения.",
         purpose_zh="以变更单方式记录数量、价格、交期与收货信息的调整，保留原值。",
         purpose_en="Records adjustments to quantity, price, delivery date "
                    "and delivery details as change notes while keeping "
                    "the original values.",
         content_ru="Выбор изменяемой позиции, сопоставление значений до и "
                    "после, причина изменения, статус подтверждения обеими "
                    "сторонами; до подтверждения прежние условия "
                    "продолжают действовать.",
         content_zh="变更项选择、变更前后值对照、变更原因、双方确认状态；未确认前原条款继续有效。",
         content_en="Selection of the item to change, before/after "
                    "comparison, reason for the change and the confirmation "
                    "status of both parties; until it is confirmed the "
                    "original terms remain in force.",
         params={"ru": "pk — идентификатор заказа",
                 "zh": "pk — 订单标识",
                 "en": "pk — order identifier"}),

    # ---------------------------------------------------------- M5
    dict(name="shipment_list", path="shipments/", view="shipment_list_view",
         module="M5", ru="Партии и перевозки", zh="运输批次列表",
         en="Shipments", access="auth",
         purpose_ru="Отслеживать состояние перевозки по партиям и "
                    "принадлежность партии каналу.",
         purpose_zh="按批次跟踪货物运输状态与所属通道。",
         purpose_en="Tracks the transport status of each shipment and the "
                    "corridor it belongs to.",
         content_ru="Список партий (номер партии, способ перевозки, канал, "
                    "пункт пропуска, текущий узел, расчётное время "
                    "прибытия); фильтр по каналу и пункту пропуска.",
         content_zh="批次列表（批次号、运输方式、通道、口岸、当前节点、预计到达时间）；支持按通道与口岸筛选。",
         content_en="Shipment list (shipment number, transport mode, "
                    "corridor, border crossing, current node, estimated "
                    "arrival); filterable by corridor and border crossing.",
         params=None),
    dict(name="shipment_detail", path="shipments/<int:pk>/",
         view="shipment_detail_view", module="M5",
         ru="Карточка партии", zh="运输节点登记", en="Shipment detail",
         access="auth",
         purpose_ru="Регистрировать узлы перевозки от получения груза до "
                    "доставки и загружать подтверждения.",
         purpose_zh="登记提货至派送的各运输节点并上传凭证。",
         purpose_en="Records each transport node from pickup to delivery "
                    "and uploads the supporting evidence.",
         content_ru="Способ перевозки и номер транспортного документа, "
                    "номер контейнера и пломбы (со сканированием), форма "
                    "регистрации узла, предупреждение об отклонении от "
                    "сроков, список подтверждений.",
         content_zh="运输方式与运单号、箱号与封号（支持扫码录入）、节点登记表单、时效偏差提示、凭证列表。",
         content_en="Transport mode and waybill number, container and seal "
                    "numbers (with barcode scanning), the node entry form, "
                    "lead-time deviation warnings and the evidence list.",
         params={"ru": "pk — идентификатор партии",
                 "zh": "pk — 运输批次标识",
                 "en": "pk — shipment identifier"}),
    dict(name="exception_list", path="exceptions/", view="exception_list_view",
         module="M5", ru="Список инцидентов", zh="在途异常列表",
         en="In-transit incidents", access="auth",
         purpose_ru="Видеть в одном месте инциденты в пути и ход их "
                    "обработки.",
         purpose_zh="集中查看在途异常及其处置进展。",
         purpose_en="Shows in-transit incidents and how they are being "
                    "handled.",
         content_ru="Список инцидентов (категория, узел возникновения, "
                    "заявитель, время сообщения, статус обработки); "
                    "необработанные инциденты закрепляются сверху и "
                    "подсвечиваются.",
         content_zh="异常列表（异常分类、发生节点、上报人、上报时间、处置状态）；未处置异常置顶并高亮。",
         content_en="Incident list (category, node where it occurred, "
                    "reporter, report time, handling status); unresolved "
                    "incidents are pinned to the top and highlighted.",
         params=None),
    dict(name="exception_create", path="exceptions/new/",
         view="exception_create_view", module="M5",
         ru="Регистрация инцидента", zh="上报在途异常",
         en="Report an incident", access="auth",
         purpose_ru="Позволить сообщить об инциденте на месте за три шага, "
                    "автоматически приложив время и местоположение.",
         purpose_zh="在现场三步内完成异常上报，自动附带时间与位置。",
         purpose_en="Lets staff report an incident on site in three steps, "
                    "automatically attaching time and location.",
         content_ru="Выбор категории инцидента, описание, загрузка "
                    "фотографий (автоматическое сжатие с записью времени и "
                    "местоположения), привязка заказа и партии; возможна "
                    "отправка офлайн с автоматической синхронизацией после "
                    "восстановления связи.",
         content_zh="异常分类选择、情况说明、拍照上传（自动压缩并记录时间与位置）、关联订单与批次；离线可提交，恢复网络后自动同步。",
         content_en="Incident category, description, photo upload "
                    "(compressed automatically with time and location "
                    "recorded) and links to the order and shipment; can be "
                    "submitted offline and syncs automatically once the "
                    "network returns.",
         params=None),

    # ---------------------------------------------------------- M6
    dict(name="documents_list", path="documents/", view="documents_list_view",
         module="M6", ru="Реестр документов", zh="单证清单",
         en="Document register", access="auth",
         purpose_ru="Показать перечень документов, необходимых для заказа, "
                    "по способу перевозки и категории товара, и их "
                    "комплектность.",
         purpose_zh="按运输方式与商品品类展示订单所需单证清单及其齐备情况。",
         purpose_en="Shows the documents an order requires, by transport "
                    "mode and goods category, and whether they are "
                    "complete.",
         content_ru="Пункты перечня (тип документа, обязательность, факт "
                    "загрузки, действующая версия, загрузивший, время "
                    "загрузки); отсутствующие пункты подсвечиваются, "
                    "рядом — переход к их добавлению.",
         content_zh="清单项（单证类型、是否必需、是否已上传、有效版本、上传人、上传时间）；缺件项高亮并给出补件入口。",
         content_en="Checklist items (document type, required or not, "
                    "uploaded or not, current valid version, uploader, "
                    "upload time); missing items are highlighted with a "
                    "shortcut for supplying them.",
         params=None),
    dict(name="documents_upload", path="documents/upload/",
         view="documents_upload_view", module="M6",
         ru="Загрузка документов", zh="单证上传", en="Upload documents",
         access="auth",
         purpose_ru="Загружать документы съёмкой, из галереи или файлом, "
                    "сохраняя все версии.",
         purpose_zh="以拍照、相册或文件三种方式上传单证，并保留版本。",
         purpose_en="Uploads documents by camera, gallery or file and keeps "
                    "every version.",
         content_ru="Выбор способа загрузки, указание типа документа, "
                    "проверка типа и размера файла, прогресс загрузки с "
                    "докачкой, маркировка версий (действующей может быть "
                    "только одна).",
         content_zh="上传方式选择、单证类型指定、文件类型与大小校验、上传进度与断点续传、版本标注（有效版本唯一）。",
         content_en="Choice of upload method, document type, file-type and "
                    "size validation, upload progress with resumable "
                    "transfers, and version labelling (only one version is "
                    "valid at a time).",
         params=None),
    dict(name="certificates_list", path="certificates/",
         view="certificates_list_view", module="M6",
         ru="Срок действия сертификатов", zh="证书有效期管理",
         en="Certificate validity", access="auth",
         purpose_ru="Вести учёт сертификатов и предупреждать о риске "
                    "истечения срока по уровням 60/30/7 дней.",
         purpose_zh="登记证书信息并按 60/30/7 天分级提醒到期风险。",
         purpose_en="Records certificate details and gives graded expiry "
                    "warnings at 60, 30 and 7 days.",
         content_ru="Список сертификатов (номер, выдавший орган, дата "
                    "начала, дата окончания, осталось дней, связанные "
                    "товары и заказы); близкие к истечению и просроченные "
                    "выделяются цветом; сертификаты, связанные с открытыми "
                    "заказами, подсвечиваются.",
         content_zh="证书列表（编号、签发方、生效日、到期日、剩余天数、关联商品与订单）；临期与过期按颜色分级；关联订单高亮。",
         content_en="Certificate list (number, issuer, effective date, "
                    "expiry date, days remaining, linked goods and orders); "
                    "near-expiry and expired certificates are colour-coded, "
                    "and certificates tied to open orders are highlighted.",
         params=None),
    dict(name="compliance_check", path="compliance/self-check/",
         view="compliance_check_view", module="M6",
         ru="Самопроверка соответствия", zh="合规自查表",
         en="Compliance self-check", access="auth",
         purpose_ru="Дать перечень для постатейной самопроверки с "
                    "сохранением следа — основание для проверки перед "
                    "отправкой.",
         purpose_zh="按清单逐项自查并留痕，作为发运前的检查依据。",
         purpose_en="Provides a checklist for item-by-item self-checking "
                    "that leaves an audit trail and serves as the "
                    "pre-shipment check.",
         content_ru="Перечень проверок, формируемый по способу перевозки, "
                    "постатейные отметки, указание причины для непройденных "
                    "пунктов, сохранение результата после отправки; "
                    "платформа только подсказывает и не выносит заключения.",
         content_zh="按运输方式生成的检查项清单、逐项勾选、不通过项填写原因、提交后生成留痕记录；平台只提示不判定结论。",
         content_en="A checklist generated from the transport mode, "
                    "item-by-item ticking, a reason field for failed items "
                    "and a recorded result on submission; the platform "
                    "only prompts, it never rules on compliance.",
         params=None),

    # ---------------------------------------------------------- M7
    dict(name="message_list", path="messages/", view="message_list_view",
         module="M7", ru="Список диалогов", zh="会话列表", en="Conversations",
         access="auth",
         purpose_ru="Показывать диалоги, сгруппированные по объектам "
                    "сделки, чтобы общение не теряло деловой контекст.",
         purpose_zh="按业务对象分组查看会话，避免沟通脱离业务上下文。",
         purpose_en="Groups conversations by business object so that "
                    "discussion never loses its business context.",
         content_ru="Список диалогов (связанный заказ / партия / документ / "
                    "акт сверки, контрагент, краткое содержание последнего "
                    "сообщения, число непрочитанных); непрочитанные "
                    "диалоги закрепляются сверху.",
         content_zh="会话列表（关联订单/批次/单证/对账单、对方企业、最后一条消息摘要、未读数）；未读会话置顶。",
         content_en="Conversation list (linked order / shipment / document "
                    "/ statement, counterparty, last-message preview, "
                    "unread count); unread conversations are pinned to the "
                    "top.",
         params=None),
    dict(name="message_detail", path="messages/<int:pk>/",
         view="message_detail_view", module="M7",
         ru="Диалог", zh="会话详情", en="Conversation detail", access="auth",
         purpose_ru="Вести двуязычное общение в контексте объекта сделки и "
                    "сохранять его историю.",
         purpose_zh="在业务对象上下文中进行中俄双语沟通并留存记录。",
         purpose_en="Carries on bilingual Chinese–Russian communication "
                    "within the context of a business object and keeps a "
                    "record of it.",
         content_ru="Лента сообщений, выбор структурированных шаблонов, "
                    "помощь с переводом (с пометкой «машинный перевод» и "
                    "подтверждением отправителя), подсказки из глоссария, "
                    "сообщения с файлами и изображениями, экспорт истории "
                    "общения по объекту сделки.",
         content_zh="消息流、结构化消息模板选择、翻译辅助（标注“机器辅助翻译”并要求发送方确认）、术语库提示、文件与图片消息、按业务对象导出沟通记录。",
         content_en="Message stream, structured message templates, "
                    "translation assistance (labelled \"machine-assisted "
                    "translation\" and requiring the sender's "
                    "confirmation), glossary hints, file and image "
                    "messages, and export of the conversation history per "
                    "business object.",
         params={"ru": "pk — идентификатор диалога",
                 "zh": "pk — 会话标识",
                 "en": "pk — conversation identifier"}),

    # ---------------------------------------------------------- M8
    dict(name="task_board", path="tasks/", view="task_board_view", module="M8",
         ru="Доска задач", zh="任务看板", en="Task board", access="auth",
         purpose_ru="Показывать задачи, сгруппированные как «на мне / "
                    "созданные мной / просроченные», с возможностью "
                    "фильтрации.",
         purpose_zh="按“待我处理 / 我发起的 / 已超时”分组呈现任务并支持筛选。",
         purpose_en="Presents tasks grouped as \"assigned to me / started "
                    "by me / overdue\" and supports filtering.",
         content_ru="Три колонки доски, карточки задач (заголовок, "
                    "связанный объект, ответственный, оставшееся время), "
                    "просроченные закрепляются сверху и подсвечиваются, "
                    "фильтрация и массовые операции.",
         content_zh="三组看板列、任务卡片（标题、关联业务对象、责任人、剩余时限）、超时项置顶并高亮、筛选与批量操作。",
         content_en="Three board columns, task cards (title, linked "
                    "business object, owner, time remaining), overdue "
                    "items pinned and highlighted, plus filtering and bulk "
                    "actions.",
         params=None),
    dict(name="task_detail", path="tasks/<int:pk>/", view="task_detail_view",
         module="M8", ru="Карточка задачи", zh="任务详情", en="Task detail",
         access="auth",
         purpose_ru="Показать подробности задачи, историю обработки и путь "
                    "эскалации.",
         purpose_zh="展示任务详情、处理记录与升级链路。",
         purpose_en="Shows the task details, its handling history and its "
                    "escalation path.",
         content_ru="Описание задачи, связанный объект, ответственный, срок "
                    "ответа, история обработки, принятие и передача задачи, "
                    "история эскалаций из-за просрочки.",
         content_zh="任务描述、关联业务对象、责任人、响应时限、处理记录、确认接收与转派、超时升级记录。",
         content_en="Task description, linked business object, owner, "
                    "response deadline, handling history, acceptance and "
                    "reassignment, and the record of escalations caused by "
                    "missed deadlines.",
         params={"ru": "pk — идентификатор задачи",
                 "zh": "pk — 任务标识",
                 "en": "pk — task identifier"}),
    dict(name="notification_settings", path="notifications/settings/",
         view="notification_settings_view", module="M8",
         ru="Настройки уведомлений", zh="提醒与免打扰设置",
         en="Notification settings", access="auth",
         purpose_ru="Настраивать каналы доставки, приоритет и часы тишины "
                    "для каждого типа событий.",
         purpose_zh="配置各类事件的推送渠道、优先级与免打扰时段。",
         purpose_en="Configures the delivery channel, priority and quiet "
                    "hours for each type of event.",
         content_ru="Типы событий и их переключатели, каналы доставки (в "
                    "приложении / СМС / почта), часы тишины (действуют по "
                    "местному времени каждого пользователя), переходы к "
                    "смене языка и часового пояса.",
         content_zh="事件类型与推送开关、推送渠道（应用内/短信/邮件）、免打扰时段（按各自本地时间生效）、语言与时区切换入口。",
         content_en="Event types and their on/off switches, delivery "
                    "channels (in-app / SMS / e-mail), quiet hours "
                    "(applied in each user's own local time), and entry "
                    "points for switching language and time zone.",
         params=None),

    # ---------------------------------------------------------- M9
    dict(name="dashboard", path="dashboard/", view="dashboard_view",
         module="M9", ru="Панель исполнения", zh="履约看板",
         en="Fulfilment dashboard", access="auth",
         purpose_ru="Показать общую картину исполнения через сводные "
                    "карточки и компактные диаграммы.",
         purpose_zh="以摘要卡与紧凑图表呈现履约整体状况。",
         purpose_en="Presents the overall state of fulfilment through "
                    "summary cards and compact charts.",
         content_ru="Количество заказов в работе, распределение по "
                    "статусам, средний цикл исполнения, список "
                    "просроченных заказов; три сводные карточки — задачи "
                    "на сегодня, проблемные заказы, сертификаты с "
                    "истекающим сроком, где каждая цифра является ссылкой.",
         content_zh="在途订单数量、状态分布、平均履约周期、超期订单清单；今日待办、异常订单、临期证书三张摘要卡，卡内数字即入口。",
         content_en="Number of orders in progress, status distribution, "
                    "average fulfilment cycle and a list of overdue "
                    "orders; three summary cards for today's tasks, "
                    "problematic orders and expiring certificates, where "
                    "each figure is itself a link.",
         params=None),
    dict(name="dashboard_logistics", path="dashboard/logistics/",
         view="dashboard_logistics_view", module="M9",
         ru="Сроки и затраты", zh="时效与成本统计",
         en="Lead time and cost", access="auth",
         purpose_ru="Считать средние сроки и структуру затрат по каналам, "
                    "пунктам пропуска и категориям.",
         purpose_zh="按通道、口岸与品类统计平均时效与费用构成。",
         purpose_en="Breaks down average lead times and cost structure by "
                    "corridor, border crossing and category.",
         content_ru="Сравнение сроков по каналам, среднее время "
                    "таможенного оформления по пунктам пропуска, структура "
                    "затрат (перевозка, таможенные сборы, хранение, "
                    "перегрузка); фильтр по периоду и экспорт.",
         content_zh="通道时效对比、口岸平均通关时长、费用构成（运费、报关费、仓储费、换装费）；支持按时间区间筛选与导出。",
         content_en="Corridor lead-time comparison, average customs "
                    "clearance time per border crossing and cost structure "
                    "(freight, customs fees, warehousing, transloading); "
                    "filterable by date range and exportable.",
         params=None),
    dict(name="dashboard_compliance", path="dashboard/compliance/",
         view="dashboard_compliance_view", module="M9",
         ru="Риски соответствия", zh="合规风险看板",
         en="Compliance risk dashboard", access="auth",
         purpose_ru="Собрать вместе сертификаты с истекающим и истёкшим "
                    "сроком, заказы с недостающими документами и "
                    "незавершённые самопроверки.",
         purpose_zh="汇总临期与过期证书、缺件订单与待完成自查项。",
         purpose_en="Brings together expiring and expired certificates, "
                    "orders with missing documents and outstanding "
                    "self-checks.",
         content_ru="Список рисков, упорядоченный по серьёзности (истёкшие "
                    "сертификаты, истекающие сертификаты, заказы с "
                    "недостающими документами, незавершённые "
                    "самопроверки), переход к обработке в один клик, "
                    "экспорт отчёта о рисках.",
         content_zh="风险清单按严重度排序（过期证书、临期证书、缺件订单、未完成自查）、一键跳转至处理页、导出风险报告。",
         content_en="Risk list ordered by severity (expired certificates, "
                    "expiring certificates, orders with missing documents, "
                    "incomplete self-checks), one-click jump to the "
                    "handling page and export of a risk report.",
         params=None),

    # ---------------------------------------------------------- M10
    dict(name="statement_list", path="statements/", view="statement_list_view",
         module="M10", ru="Список счетов", zh="账单列表", en="Statements",
         access="auth",
         purpose_ru="Формировать счета по заказам и собранным затратам и "
                    "отслеживать их подтверждение.",
         purpose_zh="依据订单与费用归集生成账单并跟踪确认状态。",
         purpose_en="Generates statements from the orders and the costs "
                    "collected against them and tracks their confirmation "
                    "status.",
         content_ru="Список счетов (связанные заказы, стоимость товара, "
                    "перевозка, таможенные сборы, хранение, итог, статус "
                    "подтверждения); фильтр по периоду и контрагенту.",
         content_zh="账单列表（关联订单、货值、运费、报关费、仓储费、合计、确认状态）；支持按时间区间与对方企业筛选。",
         content_en="Statement list (linked orders, goods value, freight, "
                    "customs fees, warehousing, total, confirmation "
                    "status); filterable by date range and counterparty.",
         params=None),
    dict(name="statement_detail", path="statements/<int:pk>/",
         view="statement_detail_view", module="M10",
         ru="Сверка расчётов", zh="对账详情", en="Reconciliation detail",
         access="auth",
         purpose_ru="Подтверждать позиции счёта по одной, отмечать "
                    "расхождения и фиксировать ход разногласий.",
         purpose_zh="逐项确认账单条目，标记差异并记录争议过程。",
         purpose_en="Confirms statement lines one by one, flags "
                    "discrepancies and records how disputes are resolved.",
         content_ru="Постатейное подтверждение, отметка расхождений с "
                    "указанием причины, регистрация этапов оплаты "
                    "(заявлена / отправлена / получена, подтверждается "
                    "каждой стороной отдельно), след разногласий и экспорт.",
         content_zh="明细逐项确认、差异标记与原因填写、付款节点状态登记（已申请/已汇出/已到账，双方分别确认）、争议留痕与导出。",
         content_en="Line-by-line confirmation, discrepancy flagging with a "
                    "reason, payment-stage registration (requested / "
                    "remitted / received, confirmed separately by each "
                    "party), and an audit trail of disputes with export.",
         params={"ru": "pk — идентификатор счёта",
                 "zh": "pk — 账单标识",
                 "en": "pk — statement identifier"}),

    # ---------------------------------------------------------- M11
    dict(name="audit_log_list", path="system/audit-logs/",
         view="audit_log_list_view", module="M11",
         ru="Журнал аудита", zh="审计日志", en="Audit log", access="role",
         purpose_ru="Искать записи о ключевых операциях: входе, изменении "
                    "прав, переходах статуса и экспорте данных.",
         purpose_zh="查询登录、权限变更、状态迁移与数据导出等关键操作记录。",
         purpose_en="Queries the record of critical operations such as "
                    "sign-ins, permission changes, status transitions and "
                    "data exports.",
         content_ru="Список записей (исполнитель, время, объект, тип "
                    "операции, значения до и после), поиск по объекту и "
                    "времени, экспорт; записи можно только читать, "
                    "удаление не предусмотрено.",
         content_zh="日志列表（操作人、时间、对象、操作类型、前后值）、按对象与时间检索、导出；日志只可查询不可删除。",
         content_en="Log list (operator, time, object, operation type, "
                    "before/after values), search by object and time, and "
                    "export; log entries can be queried but never deleted.",
         params=None),
    dict(name="dictionary_list", path="system/dictionaries/",
         view="dictionary_list_view", module="M11",
         ru="Справочники", zh="基础字典维护", en="Reference data",
         access="role",
         purpose_ru="Вести справочники пунктов пропуска, каналов, условий "
                    "поставки, типов документов и категорий причин "
                    "инцидентов.",
         purpose_zh="维护口岸、通道、贸易术语、单证类型与异常原因分类等基础字典。",
         purpose_en="Maintains reference data such as border crossings, "
                    "corridors, trade terms, document types and "
                    "incident-reason categories.",
         content_ru="Дерево категорий справочника, добавление, изменение и "
                    "удаление записей, включение и отключение, ведение "
                    "двуязычных записей; изменения записываются в журнал "
                    "аудита.",
         content_zh="字典分类树、词条增删改、启用与停用、双语词条维护；变更写入审计日志。",
         content_en="Category tree, adding, editing and deleting entries, "
                    "enabling and disabling them, and maintaining "
                    "bilingual entries; every change is written to the "
                    "audit log.",
         params=None),
    dict(name="admin_index", path="admin/", view=None, module="M11",
         ru="Административная панель Django", zh="Django 管理后台",
         en="Django admin site", access="role",
         purpose_ru="Предоставить возможности сопровождения данных через "
                    "штатную панель администратора Django.",
         purpose_zh="由 Django 框架自带的管理后台提供数据维护能力。",
         purpose_en="Provides data-maintenance capability through the "
                    "administration site that ships with the Django "
                    "framework.",
         content_ru="Регистрация моделей, создание, чтение, изменение и "
                    "удаление данных, управление пользователями и правами; "
                    "предоставляется django.contrib.admin и отдельно не "
                    "разрабатывается.",
         content_zh="模型注册、数据增删改查、用户与权限管理；由 django.contrib.admin 提供，不另行开发。",
         content_en="Model registration, CRUD on data, and user and "
                    "permission management; supplied by "
                    "django.contrib.admin and not developed separately.",
         params=None),
]

# 不带语言后缀的历史键：它们被模板
# templates/portal/page.html 和文档《应用页面
# 说明》的生成器使用。新代码应通过下方的辅助函数访问字段。
for _p in PAGES:
    _p["purpose"] = _p["purpose_zh"]
    _p["content"] = _p["content_zh"]
del _p

PAGE_BY_NAME = {p["name"]: p for p in PAGES}
PAGE_BY_VIEW = {p["view"]: p for p in PAGES if p["view"]}


def pages_of(module_code):
    return [p for p in PAGES if p["module"] == module_code]


def url_of(page):
    """用于文档的页面完整 URL（含前导斜杠）。"""
    return "/" + page["path"]


# ------------------------------------------------------- 按语言访问

def module_name(module_code, lang="ru"):
    """模块在 lang 语言下的名称（ru|zh|en）。"""
    ru, zh, en = MODULE_BY_CODE[module_code]
    return {"ru": ru, "zh": zh, "en": en}[lang]


def title_of(page, lang="ru"):
    """页面在 lang 语言下的名称。"""
    return page[lang]


def purpose_of(page, lang="ru"):
    """页面在 lang 语言下的用途。"""
    return page["purpose_" + lang]


def content_of(page, lang="ru"):
    """页面在 lang 语言下的主要内容。"""
    return page["content_" + lang]


def params_of(page, lang="ru"):
    """路由参数在 lang 语言下的说明（或 None）。"""
    return (page["params"] or {}).get(lang)


#: 页面 -> 承载它的 Django 应用（app_label）。
#: 模块与页面不是一对一：M0 的公共页留在内核，
#: 登录/注册/退出归 ``accounts``；M3 与 M4 同属 ``trading``。
#: 因此映射显式给出，而不是从 ``module`` 推导。
APP_OF = {
    "index": "core",
    "about": "core",
    "help": "core",
    "login": "accounts",
    "register": "accounts",
    "logout": "accounts",
    "enterprise_profile": "accounts",
    "enterprise_verification": "accounts",
    "enterprise_members": "accounts",
    "enterprise_invitations": "accounts",
    "goods_list": "catalog",
    "goods_detail": "catalog",
    "goods_form": "catalog",
    "rfq_list": "trading",
    "rfq_create": "trading",
    "rfq_detail": "trading",
    "quote_list": "trading",
    "quote_detail": "trading",
    "order_list": "trading",
    "order_detail": "trading",
    "order_milestones": "trading",
    "order_changes": "trading",
    "shipment_list": "logistics",
    "shipment_detail": "logistics",
    "exception_list": "logistics",
    "exception_create": "logistics",
    "documents_list": "documents",
    "documents_upload": "documents",
    "certificates_list": "documents",
    "compliance_check": "documents",
    "message_list": "messaging",
    "message_detail": "messaging",
    "task_board": "tasks",
    "task_detail": "tasks",
    "notification_settings": "tasks",
    "dashboard": "analytics",
    "dashboard_logistics": "analytics",
    "dashboard_compliance": "analytics",
    "statement_list": "billing",
    "statement_detail": "billing",
    "audit_log_list": "system",
    "dictionary_list": "system",
    "admin_index": "admin",
}


def app_of(page):
    """承载该页面的应用标签（用于 ``reverse("<app>:<name>")``）。"""
    return APP_OF[page["name"]]
