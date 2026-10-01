# -*- coding: utf-8 -*-
"""结算与对账 的路由（M10）。

路径与阶段 2《应用页面说明》中的 43 个地址一致，
拆分应用时未作任何改动；路由名与注册表 ``core/pages.py``
中的 ``name`` 相同，通过命名空间 ``billing`` 引用。
"""

from django.urls import path

from . import views

app_name = "billing"

urlpatterns = [
    path("statements/", views.statement_list_view, name="statement_list"),
    path("statements/<int:pk>/", views.statement_detail_view,
         name="statement_detail"),
]
