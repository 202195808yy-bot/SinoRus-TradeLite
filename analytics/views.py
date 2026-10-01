# -*- coding: utf-8 -*-
"""数据看板 的视图（M9）。

视图是薄壳：取注册表条目 ``core/pages.py``，
再调用数据提供器 ``analytics/datasets.py`` 组装上下文，
最后渲染 ``templates/portal/page.html``。通用逻辑在
``core/views.py``（``_page()`` / ``_page_data()`` / ``_lang()``）。
"""

from django.shortcuts import render

from core.views import _page, _page_data, _lang
from core.i18n import translate_blocks
from core.pages import PAGE_BY_NAME
from core.datasets import provider_for


from core.views import _page, _page_data, _lang
from core.i18n import translate_blocks
from core.pages import PAGE_BY_NAME
from core.datasets import provider_for

def dashboard_view(request):
    """执行面板：汇总卡片与按状态的分布。"""
    lang = _lang(request)
    data = provider_for("dashboard")(request)
    return render(request, "portal/dashboard.html", {
        "page": _page_data(PAGE_BY_NAME["dashboard"], lang),
        "prototype": False,
        "blocks": translate_blocks(data.get("blocks", []), lang),
        "mode": data.get("mode"),
    })


def dashboard_logistics_view(request):
    """时效与成本：比较渠道、口岸与类别。"""
    return _page(request, "dashboard_logistics")


def dashboard_compliance_view(request):
    """合规风险：证书与单证缺失。"""
    return _page(request, "dashboard_compliance")
