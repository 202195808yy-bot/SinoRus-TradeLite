# -*- coding: utf-8 -*-
"""平台内核 的路由（M0）。

路径与阶段 2《应用页面说明》中的 43 个地址一致，
拆分应用时未作任何改动；路由名与注册表 ``core/pages.py``
中的 ``name`` 相同，通过命名空间 ``core`` 引用。
"""

from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("lang/<str:code>/", views.set_language_view, name="set_language"),
    path("", views.index_view, name="index"),
    path("about/", views.about_view, name="about"),
    path("help/", views.help_view, name="help"),
]
