# -*- coding: utf-8 -*-
"""任务与提醒 的视图（M8）。

视图是薄壳：取注册表条目 ``core/pages.py``，
再调用数据提供器 ``tasks/datasets.py`` 组装上下文，
最后渲染 ``templates/portal/page.html``。通用逻辑在
``core/views.py``（``_page()`` / ``_page_data()`` / ``_lang()``）。
"""

from core.views import _page


def task_board_view(request):
    """任务看板：“由我处理”“我的”“已逾期”。"""
    return _page(request, "task_board")


def task_detail_view(request, pk):
    """任务卡片：期限、处理历史、升级上报。"""
    return _page(request, "task_detail", pk=pk)


def notification_settings_view(request):
    """通知、渠道与“免打扰”时段的设置。"""
    return _page(request, "notification_settings")
