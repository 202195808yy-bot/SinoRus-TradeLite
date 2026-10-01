# -*- coding: utf-8 -*-
"""询价、报价与订单 的视图（M3、M4）。

视图是薄壳：取注册表条目 ``core/pages.py``，
再调用数据提供器 ``trading/datasets.py`` 组装上下文，
最后渲染 ``templates/portal/page.html``。通用逻辑在
``core/views.py``（``_page()`` / ``_page_data()`` / ``_lang()``）。
"""

from core.views import _page


def rfq_list_view(request):
    """询价单列表：按回复状态分组。"""
    return _page(request, "rfq_list")


def rfq_create_view(request):
    """创建询价单：数量、目标价格、期限、交货地点。"""
    return _page(request, "rfq_create")


def rfq_detail_view(request, pk):
    """询价单卡片及关联的报价。"""
    return _page(request, "rfq_detail", pk=pk)


def quote_list_view(request):
    """报价列表：含版本与有效期。"""
    return _page(request, "quote_list")


def quote_detail_view(request, pk):
    """报价卡片：阶梯价格、版本、转至订单。"""
    return _page(request, "quote_detail", pk=pk)


def order_list_view(request):
    """订单列表：支持按状态筛选并突出显示异常事件。"""
    return _page(request, "order_list")


def order_detail_view(request, pk):
    """订单卡片：状态区、阶段刻度、操作区。"""
    return _page(request, "order_detail", pk=pk)


def order_milestones_view(request, pk):
    """订单执行阶段：登记与查看时间线。"""
    return _page(request, "order_milestones", pk=pk)


def order_changes_view(request, pk):
    """订单变更：需双方确认的变更单。"""
    return _page(request, "order_changes", pk=pk)
