# -*- coding: utf-8 -*-
"""单证与合规 的视图（M6）。

视图是薄壳：取注册表条目 ``core/pages.py``，
再调用数据提供器 ``documents/datasets.py`` 组装上下文，
最后渲染 ``templates/portal/page.html``。通用逻辑在
``core/views.py``（``_page()`` / ``_page_data()`` / ``_lang()``）。
"""

from core.views import _page


def documents_list_view(request):
    """单证注册表：订单单证的齐全度与配送方式。"""
    return _page(request, "documents_list")


def documents_upload_view(request):
    """上传单证：支持版本控制与断点续传。"""
    return _page(request, "documents_upload")


def certificates_list_view(request):
    """证书有效期：提前 60/30/7 天发出提醒。"""
    return _page(request, "certificates_list")


def compliance_check_view(request):
    """合规自查：记录结果的检查清单。"""
    return _page(request, "compliance_check")
