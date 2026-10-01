# -*- coding: utf-8 -*-
"""系统管理 的路由（M11）。

路径与阶段 2《应用页面说明》中的 43 个地址一致，
拆分应用时未作任何改动；路由名与注册表 ``core/pages.py``
中的 ``name`` 相同，通过命名空间 ``system`` 引用。
"""

from django.urls import path

from . import views

app_name = "system"

urlpatterns = [
    path("system/audit-logs/", views.audit_log_list_view,
         name="audit_log_list"),
    path("system/dictionaries/", views.dictionary_list_view,
         name="dictionary_list"),
]
