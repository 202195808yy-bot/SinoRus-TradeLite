# -*- coding: utf-8 -*-
"""Карточки показателей на главной странице панели.

Штатная главная страница отвечает на вопрос «что здесь вообще есть»:
список моделей. Названные цифры — «просроченных задач» или «платежей без
подтверждения» — на таком списке не видны вовсе, и узнать их можно,
только открыв нужную таблицу и проглядев её целиком. Карточки отвечают на
другой вопрос: «что требует внимания прямо сейчас».

Подписи идут через ``tr()`` (словарь ``portal/i18n.py``), как и подписи
блоков на страницах портала: это новые строки интерфейса, а не метаданные
ORM, поэтому ``langcheck.admin_labels()`` их не проверяет — за них
отвечает общий тест полноты ``portal/tests_i18n.py``.

Все подсчёты — обычные ``COUNT`` с индексом; при отсутствии таблицы
(свежая база без миграций) карточка показывает «—», а не роняет страницу.
"""

from django.db.models import Q
from django.utils import timezone

from . import models as m
from .i18n import active_lang, tr

#: Сколько дней считать «скоро истекающим» для сертификатов и документов.
EXPIRY_HORIZON_DAYS = 30


def _card(key, count, url, tone=""):
    """Карточка показателя: подпись, значение и переход по клику."""
    return {
        "key": key,
        "title": tr(key, active_lang()),
        "count": count,
        "url": url,
        "tone": tone,
    }


def _admin_url(model, **query):
    """Адрес списка модели в панели с фильтром, заданным запросом."""
    from django.urls import NoReverseMatch, reverse

    meta = model._meta
    try:
        url = reverse("admin:%s_%s_changelist" % (meta.app_label,
                                                  meta.model_name))
    except NoReverseMatch:
        return None
    if not query:
        return url
    from urllib.parse import urlencode

    return "%s?%s" % (url, urlencode(query))


def _count(qs):
    """Число записей; отсутствие таблицы даёт None, а не исключение."""
    try:
        return qs.count()
    except Exception:                        # noqa: BLE001 — БД может быть пуста
        return None


def overdue_tasks():
    """Задачи со сроком, который уже прошёл, и работа ещё не закончена."""
    today = timezone.now().date()
    return _count(m.Task.objects.filter(
        status__in=(m.Task.Status.NEW, m.Task.Status.IN_PROGRESS),
        due_date__lt=today))


def unconfirmed_payments():
    """Регистрации платежей, не подтверждённые обеими сторонами.

    Подтверждение двустороннее: закупщиком и поставщиком. Плажёж, ждущий
    вторую подпись, — это и есть незакрытый расчёт.
    """
    return _count(m.Payment.objects.filter(
        Q(buyer_confirmed=False) | Q(supplier_confirmed=False)))


def expiring_certificates():
    """Сертификаты, истекающие в ближайший месяц."""
    today = timezone.now().date()
    horizon = today + timezone.timedelta(days=EXPIRY_HORIZON_DAYS)
    return _count(m.Certificate.objects.filter(
        valid_until__gte=today, valid_until__lte=horizon))


def pending_invitations():
    """Приглашения, отправленные и ещё не принятые."""
    return _count(m.Invitation.objects.filter(
        status=m.Invitation.Status.PENDING))


def critical_incidents():
    """Инциденты высокой критичности, ещё не закрытые."""
    return _count(m.Incident.objects.filter(
        severity=m.Incident.Severity.HIGH,
        status__in=(m.Incident.Status.REGISTERED,
                    m.Incident.Status.IN_PROGRESS)))


def open_orders():
    """Заказы в работе — не завершённые и не отменённые."""
    return _count(m.Order.objects.exclude(status__in=(
        m.Order.Status.COMPLETED, m.Order.Status.CANCELED)))


#: Карточки в порядке важности. Порядок задан явно: от «требует действия
#: сейчас» к «полезно знать», чтобы взгляд сверху вниз шёл по убыванию
#: срочности.
CARDS = (
    dict(key="Задачи просроченные", value=overdue_tasks,
         url=lambda: _admin_url(m.Task, status__in="new,in_progress"),
         tone="warn"),
    dict(key="Платежи без подтверждения", value=unconfirmed_payments,
         url=lambda: _admin_url(m.Payment, buyer_confirmed="0"),
         tone="danger"),
    dict(key="Сертификаты истекают", value=expiring_certificates,
         url=lambda: _admin_url(m.Certificate), tone="warn"),
    dict(key="Инциденты критические", value=critical_incidents,
         url=lambda: _admin_url(m.Incident, severity="high"), tone="danger"),
    dict(key="Приглашения ожидают", value=pending_invitations,
         url=lambda: _admin_url(m.Invitation, status="pending"), tone=""),
    dict(key="Заказы в работе", value=open_orders,
         url=lambda: _admin_url(m.Order), tone=""),
)


def overview():
    """Карточки главной страницы. Одна ошибка не должна ронять страницу."""
    out = []
    for spec in CARDS:
        try:
            count = spec["value"]()
            url = spec["url"]()
        except Exception:                    # noqa: BLE001 — панель должна жить
            count, url = None, None
        out.append(_card(spec["key"], count, url, spec["tone"]))
    return out
