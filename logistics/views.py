# -*- coding: utf-8 -*-
"""物流与口岸 的视图（M5）。

视图是薄壳：取注册表条目 ``core/pages.py``，
再调用数据提供器 ``logistics/datasets.py`` 组装上下文，
最后渲染 ``templates/portal/page.html``。通用逻辑在
``core/views.py``（``_page()`` / ``_page_data()`` / ``_lang()``）。
"""

from core.views import _page


def shipment_list_view(request):
    """批次与运输：按批次跟踪状态。"""
    return _page(request, "shipment_list")


def shipment_detail_view(request, pk):
    """批次卡片：登记运输阶段与单证。"""
    return _page(request, "shipment_detail", pk=pk)


def exception_list_view(request):
    """在途异常事件列表及其处理进展。"""
    return _page(request, "exception_list")


def exception_create_view(request):
    """异常事件登记：照片、描述、时间与地点。"""
    return _page(request, "exception_create")
