# -*- coding: utf-8 -*-
"""物流与口岸 的路由（M5）。

路径与阶段 2《应用页面说明》中的 43 个地址一致，
拆分应用时未作任何改动；路由名与注册表 ``core/pages.py``
中的 ``name`` 相同，通过命名空间 ``logistics`` 引用。
"""

from django.urls import path

from . import views

app_name = "logistics"

urlpatterns = [
    path("shipments/", views.shipment_list_view, name="shipment_list"),
    path("shipments/<int:pk>/", views.shipment_detail_view,
         name="shipment_detail"),
    path("exceptions/", views.exception_list_view, name="exception_list"),
    path("exceptions/new/", views.exception_create_view,
         name="exception_create"),
]
