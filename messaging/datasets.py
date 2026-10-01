# -*- coding: utf-8 -*-
"""双语沟通 的页面数据提供器。

区块构造器与工具函数在 ``core/datasets.py``；
这里只放本应用页面自己的取数逻辑，并在模块末尾
用 ``PROVIDERS`` 声明页面名到提供器的映射。
"""

from decimal import Decimal

from django.shortcuts import get_object_or_404
from django.db.models import Count

from core.datasets import (badge_of, c, dtm, fld, k, kpi, num, tbl)
from messaging.models import Dialog, Message, Translation


def message_list_data(request, **kw):
    qs = (Dialog.objects
          .annotate(n_messages=Count("messages"))
          .order_by("-last_message_at"))
    blocks = [
        kpi("Диалоги", [
            k("Всего", Dialog.objects.count()),
            k("Открытых", Dialog.objects.filter(status="open").count()),
            k("Сообщений", Message.objects.count()),
            k("Переводов", Translation.objects.count(), "выполнено"),
        ]),
        tbl("Диалоги по бизнес-объектам",
            ["Объект", "Обозначение", "Сообщений", "Последнее сообщение",
             "Статус"],
            [[c(d.get_subject_kind_display()),
              c(d.subject_label or "—"),
              c(num(d.n_messages)), c(dtm(d.last_message_at)),
              badge_of(d.status, d.get_status_display())]
             for d in qs],
            empty="Диалоги не начаты"),
    ]
    return {"blocks": blocks}


def message_detail_data(request, pk, **kw):
    d = get_object_or_404(Dialog.objects, pk=pk)
    messages = d.messages.select_related("author").order_by("created_at")
    blocks = [
        fld("Диалог", [
            ("Объект", d.get_subject_kind_display()),
            ("Обозначение", d.subject_label or "—"),
            ("Статус", d.get_status_display()),
            ("Последнее сообщение", dtm(d.last_message_at)),
            ("Участники", ", ".join(
                u.get_username() for u in d.participants.all()) or "—"),
        ]),
        tbl("Сообщения",
            ["Время", "Автор", "Язык", "Текст"],
            [[c(dtm(msg.created_at)), c(msg.author.get_username()),
              c(msg.get_language_display()), c(msg.body)]
             for msg in messages],
            empty="Сообщений нет"),
        tbl("Переводы",
            ["Сообщение", "С языка", "На язык", "Перевод", "Движок"],
            [[c(f"#{tr.message_id}", mono=True),
              c(tr.source_language), c(tr.target_language),
              c(tr.text), c(tr.engine or "—")]
             for tr in Translation.objects.filter(
                 message__dialog=d).select_related("message")],
            empty="Переводы не выполнялись"),
    ]
    return {"blocks": blocks}


#: 本应用页面的提供器（在 ``apps.ready()`` 中登记）。
PROVIDERS = {
    "message_detail": message_detail_data,
    "message_list": message_list_data,
}
