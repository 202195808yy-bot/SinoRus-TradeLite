# -*- coding: utf-8 -*-
"""任务与提醒 的页面数据提供器。

区块构造器与工具函数在 ``core/datasets.py``；
这里只放本应用页面自己的取数逻辑，并在模块末尾
用 ``PROVIDERS`` 声明页面名到提供器的映射。
"""

from decimal import Decimal

from django.shortcuts import get_object_or_404
from django.utils import timezone

from core.datasets import (badge_of, c, dt, dtm, fld, k, kpi, safe, tbl, url_for)
from tasks.models import Notification, NotificationSetting, Task


def task_board_data(request, **kw):
    today = timezone.now().date()
    qs = Task.objects.select_related("assignee")
    overdue = [t for t in qs if t.is_overdue]
    blocks = [
        kpi("Доска задач", [
            k("Новых", qs.filter(status="new").count()),
            k("В работе", qs.filter(status="in_progress").count()),
            k("Просрочено", len(overdue), tone="danger"),
            k("Выполнено", qs.filter(status="done").count(), tone="ok"),
        ]),
        tbl("Просроченные задачи",
            ["Номер", "Заголовок", "Исполнитель", "Срок", "Приоритет",
             "Статус"],
            [[c(t.number, url_for("task_detail", t.pk), mono=True),
              c(t.title), c(safe(t.assignee, "get_username", "—")),
              c(dt(t.due_date)),
              badge_of(t.priority, t.get_priority_display()),
              badge_of(t.status, t.get_status_display())]
             for t in overdue],
            empty="Просроченных задач нет"),
        tbl("Все задачи",
            ["Номер", "Заголовок", "Источник", "Исполнитель", "Срок",
             "Приоритет", "Статус"],
            [[c(t.number, url_for("task_detail", t.pk), mono=True),
              c(t.title),
              c(f"{t.get_source_kind_display()} #{t.source_id}"
                if t.source_id else t.get_source_kind_display()),
              c(safe(t.assignee, "get_username", "—")), c(dt(t.due_date)),
              badge_of(t.priority, t.get_priority_display()),
              badge_of(t.status, t.get_status_display())]
             for t in qs.order_by("due_date")],
            empty="Задач нет"),
    ]
    return {"blocks": blocks}


def task_detail_data(request, pk, **kw):
    t = get_object_or_404(Task.objects.select_related("assignee"), pk=pk)
    blocks = [
        fld("Карточка задачи", [
            ("Номер", t.number),
            ("Заголовок", t.title),
            ("Источник", f"{t.get_source_kind_display()} #{t.source_id}"
             if t.source_id else t.get_source_kind_display()),
            ("Исполнитель", safe(t.assignee, "get_username", "—")),
            ("Срок", dt(t.due_date)),
            ("Приоритет", t.get_priority_display()),
            ("Статус", t.get_status_display()),
            ("Просрочена", "да" if t.is_overdue else "нет"),
            ("Создана", dt(t.created_at)),
        ]),
        tbl("Напоминания",
            ["Канал", "Время отправки", "Отправлено"],
            [[badge_of(r.channel, r.get_channel_display()),
              c(dtm(r.send_at)), c("да" if r.is_sent else "нет")]
             for r in t.reminders.all()],
            empty="Напоминания не настроены"),
    ]
    return {"blocks": blocks}


def notification_settings_data(request, **kw):
    qs = NotificationSetting.objects.select_related("user")
    blocks = [
        tbl("Настройки уведомлений",
            ["Пользователь", "Событие", "Канал", "Включено"],
            [[c(s.user.get_username()),
              badge_of(s.event, s.get_event_display()),
              badge_of(s.channel, s.get_channel_display()),
              c("да" if s.is_enabled else "нет")]
             for s in qs],
            empty="Настройки не заданы"),
        tbl("Последние уведомления",
            ["Получатель", "Вид", "Заголовок", "Прочитано", "Создано"],
            [[c(n.recipient.get_username()), c(n.kind), c(n.title),
              c("да" if n.is_read else "нет"), c(dtm(n.created_at))]
             for n in Notification.objects.select_related(
                 "recipient").order_by("-created_at")[:20]],
            empty="Уведомлений нет"),
    ]
    return {"blocks": blocks}


#: 本应用页面的提供器（在 ``apps.ready()`` 中登记）。
PROVIDERS = {
    "notification_settings": notification_settings_data,
    "task_board": task_board_data,
    "task_detail": task_detail_data,
}
