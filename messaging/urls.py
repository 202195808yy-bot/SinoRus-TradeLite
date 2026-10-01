# -*- coding: utf-8 -*-
"""双语沟通 的路由（M7）。

路径与阶段 2《应用页面说明》中的 43 个地址一致，
拆分应用时未作任何改动；路由名与注册表 ``core/pages.py``
中的 ``name`` 相同，通过命名空间 ``messaging`` 引用。
"""

from django.urls import path

from . import views

app_name = "messaging"

urlpatterns = [
    path("messages/", views.message_list_view, name="message_list"),
    path("messages/<int:pk>/", views.message_detail_view,
         name="message_detail"),
]
