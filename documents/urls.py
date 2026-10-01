# -*- coding: utf-8 -*-
"""单证与合规 的路由（M6）。

路径与阶段 2《应用页面说明》中的 43 个地址一致，
拆分应用时未作任何改动；路由名与注册表 ``core/pages.py``
中的 ``name`` 相同，通过命名空间 ``documents`` 引用。
"""

from django.urls import path

from . import views

app_name = "documents"

urlpatterns = [
    path("documents/", views.documents_list_view, name="documents_list"),
    path("documents/upload/", views.documents_upload_view,
         name="documents_upload"),
    path("certificates/", views.certificates_list_view,
         name="certificates_list"),
    path("compliance/self-check/", views.compliance_check_view,
         name="compliance_check"),
]
