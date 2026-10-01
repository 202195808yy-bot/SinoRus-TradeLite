# -*- coding: utf-8 -*-
"""数据看板 的路由（M9）。

路径与阶段 2《应用页面说明》中的 43 个地址一致，
拆分应用时未作任何改动；路由名与注册表 ``core/pages.py``
中的 ``name`` 相同，通过命名空间 ``analytics`` 引用。
"""

from django.urls import path

from . import views

app_name = "analytics"

urlpatterns = [
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("dashboard/logistics/", views.dashboard_logistics_view,
         name="dashboard_logistics"),
    path("dashboard/compliance/", views.dashboard_compliance_view,
         name="dashboard_compliance"),
]
