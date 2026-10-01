# -*- coding: utf-8 -*-
"""询价、报价与订单 的路由（M3、M4）。

路径与阶段 2《应用页面说明》中的 43 个地址一致，
拆分应用时未作任何改动；路由名与注册表 ``core/pages.py``
中的 ``name`` 相同，通过命名空间 ``trading`` 引用。
"""

from django.urls import path

from . import views

app_name = "trading"

urlpatterns = [
    path("rfqs/", views.rfq_list_view, name="rfq_list"),
    path("rfqs/new/", views.rfq_create_view, name="rfq_create"),
    path("rfqs/<int:pk>/", views.rfq_detail_view, name="rfq_detail"),
    path("quotes/", views.quote_list_view, name="quote_list"),
    path("quotes/<int:pk>/", views.quote_detail_view, name="quote_detail"),
    path("orders/", views.order_list_view, name="order_list"),
    path("orders/<int:pk>/", views.order_detail_view, name="order_detail"),
    path("orders/<int:pk>/milestones/", views.order_milestones_view,
         name="order_milestones"),
    path("orders/<int:pk>/changes/", views.order_changes_view,
         name="order_changes"),
]
