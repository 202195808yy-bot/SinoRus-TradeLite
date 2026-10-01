# -*- coding: utf-8 -*-
"""商品与参考字典 的视图（M2）。

视图是薄壳：取注册表条目 ``core/pages.py``，
再调用数据提供器 ``catalog/datasets.py`` 组装上下文，
最后渲染 ``templates/portal/page.html``。通用逻辑在
``core/views.py``（``_page()`` / ``_page_data()`` / ``_lang()``）。
"""

from core.views import _page


def goods_list_view(request):
    """商品列表：支持筛选与卡片式展示。"""
    return _page(request, "goods_list")


def goods_detail_view(request, pk):
    """商品卡片：特性、合规、版本历史。"""
    return _page(request, "goods_detail", pk=pk)


def goods_form_view(request):
    """以分步表单创建和编辑商品。"""
    return _page(request, "goods_form")
