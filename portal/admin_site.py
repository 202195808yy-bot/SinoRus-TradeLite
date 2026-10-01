# -*- coding: utf-8 -*-
"""自定义面板站点：模型的业务分组与记录计数。

面板自带的主页按 Django 应用对模型分组，
并按翻译后的名称排序。对本平台来说这不方便：

* “用户与组”和“跨境贸易门户”两组
  反映的是项目结构，而非用户的业务内容；
* 顺序由翻译计算得出，因此切换语言时所有
  行的位置都会跳动，肌肉记忆随之失效。

因此重写了 ``get_app_list()``：分组显式指定，顺序
固定，并为每个模型添加了记录计数。

复用自带的 ``_build_app_dict()``：它已经计算权限、
构造地址，并剔除用户无权访问的模型。
自行组装字典会重复这套逻辑，并且会在 Django
升级时与它产生分歧。

通过 ``default_site`` 接入（见 ``portal/apps.py``）：站点
在 ``autodiscover()`` 执行所有 ``@admin.register`` 之前就被替换。
"""

from django.contrib.admin.sites import AdminSite
from django.utils import translation

from .i18n import DEFAULT_LANG, normalize

#: 组以及组内模型的顺序是显式指定的，不依赖语言。
#: 逻辑是交易的生命周期：先是参与方，然后是商品，接着是
#: 询价、订单、配送、文档、沟通、结算，最后是
#: 技术类。组内则从聚合根出发，到它的字典
#: 和从属表。
ADMIN_GROUPS = (
    dict(key="parties", ru="Субъекты и учётные записи", zh="主体与账号",
         en="Parties and accounts", models=(
             "Enterprise", "Industry", "Counterparty",
             "Membership", "Invitation", "Profile")),
    dict(key="catalog", ru="Товары и справочники", zh="商品与基础数据",
         en="Goods and master data", models=(
             "Good", "GoodCategory", "Uom", "Packaging", "ProductImage",
             "Country", "Currency")),
    dict(key="quoting", ru="Запросы котировки и предложения", zh="询价与报价",
         en="RFQs and quotes", models=("Rfq", "Quote", "QuoteVersion")),
    dict(key="orders", ru="Заказы и исполнение", zh="订单与执行",
         en="Orders and fulfilment", models=(
             "Order", "OrderMilestone", "OrderChange")),
    dict(key="logistics", ru="Логистика и таможня", zh="物流与口岸",
         en="Logistics and customs", models=(
             "Shipment", "Transport", "TrackPoint", "Incident",
             "TransportLane", "BorderCrossing", "Tariff")),
    dict(key="documents", ru="Документы и соответствие", zh="单证与合规",
         en="Documents and compliance", models=(
             "DocType", "Document", "Certificate", "DocRequirement",
             "ComplianceCheck", "DeadlineReminder")),
    dict(key="communication", ru="Двуязычное общение", zh="双语沟通",
         en="Bilingual communication", models=(
             "Dialog", "Message", "Translation", "Attachment")),
    dict(key="work", ru="Задачи, уведомления и расчёты", zh="任务、通知与结算",
         en="Tasks, notifications and settlements", models=(
             "Task", "TaskReminder", "Notification", "NotificationSetting",
             "Statement", "Payment", "Reconciliation")),
    dict(key="system", ru="Система, аналитика и риски", zh="系统、分析与风险",
         en="System, analytics and risks", models=(
             "Metric", "MetricSnapshot", "ComplianceRisk",
             "AuditLog", "SystemParam", "User", "Group")),
)

#: 默认折叠的组：技术实体和访问权限。
COLLAPSED = frozenset({"system"})


def active_lang():
    """界面语言，以应用代码表示（``ru`` / ``zh`` / ``en``）。"""
    return normalize(translation.get_language()) or DEFAULT_LANG


def group_label(group, lang):
    """分组名称使用界面语言。

    分组名称不是 ORM 元数据，因此 ``langcheck.admin_labels()``
    不会遍历它们，面板的标签字典也不认识它们：翻译是自带的，
    否则未翻译的字符串会悄悄进入中文界面。
    """
    if lang == "zh":
        return group["zh"]
    if lang == "en":
        return group["en"]
    return group["ru"]


def record_count(model):
    """模型的记录数。表不存在时不应使页面崩溃。"""
    try:
        return model.objects.count()
    except Exception:                        # noqa: BLE001 ——数据库可能为空
        return None


class TradeHubAdminSite(AdminSite):
    """带有业务分组与记录计数的面板。"""

    def get_app_list(self, request, app_label=None):
        """具有固定顺序和记录计数的模型分组。

        自带的 ``app_dict`` 只构建一次，再分发到各组：
        权限、地址和访问过滤仍沿用 Django 的逻辑。计数器
        每个模型只计算一次——主页上对 SQLite 的 50 次 ``COUNT`` 查询
        无足轻重，换来的是用户无需打开表格就能看出
        表格是空是满。
        """
        # app_label 已在应用页面 (/admin/portal/) 上指定：那里
        # 需要按单个应用做标准分组，否则标题
        # 和列表会错位。
        if app_label:
            return super().get_app_list(request, app_label)

        lang = active_lang()
        built = {}
        for entry in self._build_app_dict(request).values():
            for item in entry["models"]:
                built[item["model"].__name__] = item

        groups = []
        for group in ADMIN_GROUPS:
            models = []
            for name in group["models"]:
                item = built.get(name)
                if item is None:             # 没有权限或未注册
                    continue
                item = dict(item)
                item["count"] = record_count(item["model"])
                models.append(item)
            if not models:
                continue
            groups.append({
                "key": group["key"],
                "name": group_label(group, lang),
                "app_label": group["key"],
                "app_url": None,
                "has_module_perms": True,
                "collapsed": group["key"] in COLLAPSED,
                "models": models,
            })
        return groups

    def index(self, request, extra_context=None):
        """主页：分组加指标卡片。"""
        from django.template.response import TemplateResponse

        from .admin_kpi import overview
        from .i18n import tr

        context = {
            **self.each_context(request),
            "title": self.index_title,
            "subtitle": None,
            "app_list": self.get_app_list(request),
            "kpi": overview(),
            # 卡片区块的标题来自标签字典，而不是通过
            # ``{% translate %}``：面板中不属于 Django 发布包的字符串
            # 在其他语言下会保持为俄语。
            "kpi_title": tr("Требуют внимания", active_lang()),
            **(extra_context or {}),
        }
        request.current_app = self.name
        return TemplateResponse(
            request, self.index_template or "admin/index.html", context)
