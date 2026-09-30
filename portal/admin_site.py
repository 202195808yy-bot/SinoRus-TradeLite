# -*- coding: utf-8 -*-
"""Свой сайт панели: бизнес-группировка моделей и счётчики записей.

Штатная главная страница панели группирует модели по приложениям Django
и сортирует их по переведённому имени. Для платформы это неудобно:

* две группы — «Пользователи и группы» и «Портал трансграничной торговли» —
  отражают устройство проекта, а не то, чем занимается пользователь;
* порядок вычисляется из перевода, поэтому при смене языка позиции всех
  строк скачут и мышечная память перестаёт работать.

Поэтому ``get_app_list()`` переопределён: группы заданы явно, их порядок
фиксирован, а у каждой модели добавлен счётчик записей.

Переиспользуется штатный ``_build_app_dict()``: он уже считает права,
строит адреса и отбрасывает модели, к которым у пользователя нет доступа.
Своя сборка словаря продублировала бы эту логику и разошлась с ней при
обновлении Django.

Подключение — через ``default_site`` (см. ``portal/apps.py``): сайт
подменяется раньше, чем ``autodiscover()`` выполнит все ``@admin.register``.
"""

from django.contrib.admin.sites import AdminSite
from django.utils import translation

from .i18n import DEFAULT_LANG, normalize

#: Порядок групп и моделей внутри них задан явно и не зависит от языка.
#: Логика — жизненный цикл сделки: сначала стороны, потом товар, затем
#: запрос цены, заказ, доставка, документы, общение, расчёты и, наконец,
#: техническое. Внутри группы — от агрегирующего корня к его справочникам
#: и подчинённым таблицам.
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

#: Группы, свёрнутые по умолчанию: технические сущности и права доступа.
COLLAPSED = frozenset({"system"})


def active_lang():
    """Язык интерфейса в виде кода приложения (``ru`` / ``zh`` / ``en``)."""
    return normalize(translation.get_language()) or DEFAULT_LANG


def group_label(group, lang):
    """Название группы на языке интерфейса.

    Названия групп — не метаданные ORM, поэтому ``langcheck.admin_labels()``
    их не обходит и словарь подписей панели их не знает: перевод свой,
    иначе непереведённая строка молча уехала бы в китайский интерфейс.
    """
    if lang == "zh":
        return group["zh"]
    if lang == "en":
        return group["en"]
    return group["ru"]


def record_count(model):
    """Число записей модели. Отсутствие таблицы не должно ронять страницу."""
    try:
        return model.objects.count()
    except Exception:                        # noqa: BLE001 — БД может быть пуста
        return None


class TradeHubAdminSite(AdminSite):
    """Панель с бизнес-группировкой и счётчиками записей."""

    def get_app_list(self, request, app_label=None):
        """Группы моделей с фиксированным порядком и счётчиками.

        Штатные ``app_dict`` строятся один раз и раскладываются по группам:
        права, адреса и отсев по доступу остаются от Django. Счётчик
        считается один раз на модель — 50 запросов ``COUNT`` к SQLite на
        главной странице несущественны, а взамен пользователь видит, пустая
        таблица или полная, не открывая её.
        """
        # app_label задан на странице приложения (/admin/portal/): там
        # нужна штатная группировка по одному приложению, иначе заголовок
        # и список разъедутся.
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
                if item is None:             # нет прав или не зарегистрирована
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
        """Главная страница: группы плюс карточки показателей."""
        from django.template.response import TemplateResponse

        from .admin_kpi import overview
        from .i18n import tr

        context = {
            **self.each_context(request),
            "title": self.index_title,
            "subtitle": None,
            "app_list": self.get_app_list(request),
            "kpi": overview(),
            # Заголовок блока карточек — из словаря подписей, а не через
            # ``{% translate %}``: строки панели, которых нет в поставке
            # Django, на других языках остались бы русскими.
            "kpi_title": tr("Требуют внимания", active_lang()),
            **(extra_context or {}),
        }
        request.current_app = self.name
        return TemplateResponse(
            request, self.index_template or "admin/index.html", context)
