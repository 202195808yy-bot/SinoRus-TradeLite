# -*- coding: utf-8 -*-
"""商品与参考字典 的路由（M2）。

路径与阶段 2《应用页面说明》中的 43 个地址一致，
拆分应用时未作任何改动；路由名与注册表 ``core/pages.py``
中的 ``name`` 相同，通过命名空间 ``catalog`` 引用。
"""

from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("goods/", views.goods_list_view, name="goods_list"),
    path("goods/<int:pk>/", views.goods_detail_view, name="goods_detail"),
    path("goods/new/", views.goods_form_view, name="goods_form"),
]
