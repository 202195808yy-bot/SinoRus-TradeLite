# -*- coding: utf-8 -*-
"""系统管理 的视图（M11）。

视图是薄壳：取注册表条目 ``core/pages.py``，
再调用数据提供器 ``system/datasets.py`` 组装上下文，
最后渲染 ``templates/portal/page.html``。通用逻辑在
``core/views.py``（``_page()`` / ``_page_data()`` / ``_lang()``）。
"""

from core.views import _page


def audit_log_list_view(request):
    """审计日志：关键操作，只读。"""
    return _page(request, "audit_log_list")


def dictionary_list_view(request):
    """字典：口岸、渠道、术语、单证类型。"""
    return _page(request, "dictionary_list")
