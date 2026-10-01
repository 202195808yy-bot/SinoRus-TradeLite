# -*- coding: utf-8 -*-
"""结算与对账 的视图（M10）。

视图是薄壳：取注册表条目 ``core/pages.py``，
再调用数据提供器 ``billing/datasets.py`` 组装上下文，
最后渲染 ``templates/portal/page.html``。通用逻辑在
``core/views.py``（``_page()`` / ``_page_data()`` / ``_lang()``）。
"""

from core.views import _page


def statement_list_view(request):
    """按订单和费用生成的账单列表。"""
    return _page(request, "statement_list")


def statement_detail_view(request, pk):
    """结算对账：逐项确认与差异。"""
    return _page(request, "statement_detail", pk=pk)
