# -*- coding: utf-8 -*-
"""Представления приложения portal.

Этап 4 («Шаблоны страниц приложения»). Каждое представление соответствует
одной странице реестра ``portal/pages.py`` и получает данные из моделей
через провайдеры ``portal/datasets.py``.

Страницы, для которых провайдер ещё не написан, отрисовываются как
прототипы (заглушка вместо данных) — см. ``datasets.coverage()``.
"""

from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect, render

from .datasets import provider_for
from .i18n import DEFAULT_LANG, translate_blocks
from .pages import (PAGE_BY_NAME, PAGES, content_of, module_name, params_of,
                    purpose_of, title_of)


def _lang(request):
    """Текущий язык интерфейса (см. portal.middleware.LanguageMiddleware)."""
    return getattr(request, "LANG", DEFAULT_LANG)


def _page_data(page, lang):
    """Запись реестра с названием и описанием на текущем языке.

    Поля ``ru``/``zh``/``en`` сохраняются: шаблон показывает второй язык
    подсказкой. Исторические ключи ``purpose``/``content`` (синонимы
    китайских вариантов) перекрываются переводами текущего языка — так
    страница больше не смешивает русский заголовок с китайским текстом.
    """
    data = dict(page)
    data["title"] = title_of(page, lang)
    data["purpose"] = purpose_of(page, lang)
    data["content"] = content_of(page, lang)
    data["params"] = params_of(page, lang)
    data["module_title"] = module_name(page["module"], lang)
    data["module_alt"] = module_name(
        page["module"], "ru" if lang == "zh" else "zh")
    return data


def _page(request, name, **extra):
    """Отрисовка страницы по записи реестра и провайдеру данных."""
    lang = _lang(request)
    page = PAGE_BY_NAME[name]
    provider = provider_for(name)
    context = {
        "page": _page_data(page, lang),
        "page_url": "/" + page["path"],
        "all_pages": PAGES,
        "prototype": provider is None,
        "blocks": [],
        "mode": None,
    }
    if provider is not None:
        data = provider(request, **extra) or {}
        context["blocks"] = translate_blocks(data.get("blocks", []), lang)
        context["mode"] = data.get("mode")
    context.update(extra)
    return render(request, "portal/page.html", context)



# ======================================================================
# M0. Общие страницы
# ======================================================================

def index_view(request):
    """Главная страница: сводка платформы и последние заказы."""
    lang = _lang(request)
    data = provider_for("index")(request)
    return render(request, "portal/index.html", {
        "page": _page_data(PAGE_BY_NAME["index"], lang),
        "prototype": False,
        "blocks": translate_blocks(data.get("blocks", []), lang),
        "mode": data.get("mode"),
    })


def about_view(request):
    """Сведения о платформе и границах её предметной области."""
    return _page(request, "about")


def help_view(request):
    """Справка: инструкции по ролям и ответы на частые вопросы."""
    return _page(request, "help")


def login_view(request):
    """Вход в систему. Прототип формы аутентификации."""
    return _page(request, "login")


def register_view(request):
    """Регистрация нового пользователя с привязкой к предприятию."""
    return _page(request, "register")


def logout_view(request):
    """Выход из системы с завершением сессии."""
    auth_logout(request)
    return redirect("portal:index")


# ======================================================================
# M1. Предприятие и аккаунт
# ======================================================================

def enterprise_profile_view(request):
    """Профиль предприятия: двуязычные реквизиты и контактные данные."""
    return _page(request, "enterprise_profile")


def enterprise_verification_view(request):
    """Подтверждение субъекта: загрузка документов и статус проверки."""
    return _page(request, "enterprise_verification")


def enterprise_members_view(request):
    """Сотрудники и роли: состав организации и назначение ролей."""
    return _page(request, "enterprise_members")


def enterprise_invitations_view(request):
    """Приглашение партнёров в область совместной работы по заказу."""
    return _page(request, "enterprise_invitations")


# ======================================================================
# M2. Товары
# ======================================================================

def goods_list_view(request):
    """Список товаров с фильтрацией и карточным представлением."""
    return _page(request, "goods_list")


def goods_detail_view(request, pk):
    """Карточка товара: характеристики, соответствие, история версий."""
    return _page(request, "goods_detail", pk=pk)


def goods_form_view(request):
    """Создание и редактирование товара пошаговой формой."""
    return _page(request, "goods_form")


# ======================================================================
# M3. Запросы и предложения
# ======================================================================

def rfq_list_view(request):
    """Список запросов, сгруппированный по статусу ответа."""
    return _page(request, "rfq_list")


def rfq_create_view(request):
    """Создание запроса: количество, целевая цена, срок, место доставки."""
    return _page(request, "rfq_create")


def rfq_detail_view(request, pk):
    """Карточка запроса со связанными предложениями."""
    return _page(request, "rfq_detail", pk=pk)


def quote_list_view(request):
    """Список предложений с версиями и сроками действия."""
    return _page(request, "quote_list")


def quote_detail_view(request, pk):
    """Карточка предложения: ступенчатые цены, версии, переход к заказу."""
    return _page(request, "quote_detail", pk=pk)


# ======================================================================
# M4. Заказы
# ======================================================================

def order_list_view(request):
    """Список заказов с фильтрацией по статусу и выделением инцидентов."""
    return _page(request, "order_list")


def order_detail_view(request, pk):
    """Карточка заказа: зона состояния, шкала этапов, зона действий."""
    return _page(request, "order_detail", pk=pk)


def order_milestones_view(request, pk):
    """Этапы исполнения заказа: регистрация и просмотр хронологии."""
    return _page(request, "order_milestones", pk=pk)


def order_changes_view(request, pk):
    """Изменения заказа: листы изменений с подтверждением сторон."""
    return _page(request, "order_changes", pk=pk)


# ======================================================================
# M5. Логистика и пункты пропуска
# ======================================================================

def shipment_list_view(request):
    """Партии и перевозки: отслеживание состояния по партиям."""
    return _page(request, "shipment_list")


def shipment_detail_view(request, pk):
    """Карточка партии: регистрация этапов перевозки и документов."""
    return _page(request, "shipment_detail", pk=pk)


def exception_list_view(request):
    """Список инцидентов в пути и ход их обработки."""
    return _page(request, "exception_list")


def exception_create_view(request):
    """Регистрация инцидента: фотография, описание, время и место."""
    return _page(request, "exception_create")


# ======================================================================
# M6. Документы и соответствие
# ======================================================================

def documents_list_view(request):
    """Реестр документов: комплектность по заказу и способ доставки."""
    return _page(request, "documents_list")


def documents_upload_view(request):
    """Загрузка документов с контролем версий и возобновлением передачи."""
    return _page(request, "documents_upload")


def certificates_list_view(request):
    """Срок действия сертификатов с напоминаниями за 60/30/7 дней."""
    return _page(request, "certificates_list")


def compliance_check_view(request):
    """Самопроверка соответствия: чек-лист с фиксацией результата."""
    return _page(request, "compliance_check")


# ======================================================================
# M7. Двуязычное общение
# ======================================================================

def message_list_view(request):
    """Список диалогов, сгруппированных по бизнес-объектам."""
    return _page(request, "message_list")


def message_detail_view(request, pk):
    """Диалог в контексте бизнес-объекта с помощью перевода."""
    return _page(request, "message_detail", pk=pk)


# ======================================================================
# M8. Задачи и напоминания
# ======================================================================

def task_board_view(request):
    """Доска задач: «на мне», «мои», «просроченные»."""
    return _page(request, "task_board")


def task_detail_view(request, pk):
    """Карточка задачи: сроки, история обработки, эскалация."""
    return _page(request, "task_detail", pk=pk)


def notification_settings_view(request):
    """Настройки уведомлений, каналов и периодов «не беспокоить»."""
    return _page(request, "notification_settings")


# ======================================================================
# M9. Аналитика
# ======================================================================

def dashboard_view(request):
    """Панель исполнения: сводные карточки и распределение по статусам."""
    lang = _lang(request)
    data = provider_for("dashboard")(request)
    return render(request, "portal/dashboard.html", {
        "page": _page_data(PAGE_BY_NAME["dashboard"], lang),
        "prototype": False,
        "blocks": translate_blocks(data.get("blocks", []), lang),
        "mode": data.get("mode"),
    })


def dashboard_logistics_view(request):
    """Сроки и затраты: сравнение каналов, пунктов пропуска и категорий."""
    return _page(request, "dashboard_logistics")


def dashboard_compliance_view(request):
    """Риски соответствия: сертификаты и нехватка документов."""
    return _page(request, "dashboard_compliance")


# ======================================================================
# M10. Расчёты и сверка
# ======================================================================

def statement_list_view(request):
    """Список счетов, сформированных по заказам и затратам."""
    return _page(request, "statement_list")


def statement_detail_view(request, pk):
    """Сверка расчётов: постатейное подтверждение и разногласия."""
    return _page(request, "statement_detail", pk=pk)


# ======================================================================
# M11. Администрирование
# ======================================================================

def audit_log_list_view(request):
    """Журнал аудита: ключевые действия, только для чтения."""
    return _page(request, "audit_log_list")


def dictionary_list_view(request):
    """Справочники: пункты пропуска, каналы, термины, типы документов."""
    return _page(request, "dictionary_list")
