# -*- coding: utf-8 -*-
"""双语沟通 的视图（M7）。

视图是薄壳：取注册表条目 ``core/pages.py``，
再调用数据提供器 ``messaging/datasets.py`` 组装上下文，
最后渲染 ``templates/portal/page.html``。通用逻辑在
``core/views.py``（``_page()`` / ``_page_data()`` / ``_lang()``）。
"""

from core.views import _page


def message_list_view(request):
    """对话列表：按业务对象分组。"""
    return _page(request, "message_list")


def message_detail_view(request, pk):
    """业务对象上下文中的对话，辅以翻译。"""
    return _page(request, "message_detail", pk=pk)
