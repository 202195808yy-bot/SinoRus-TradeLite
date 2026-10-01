# -*- coding: utf-8 -*-
"""企业与账号 的路由（M0、M1）。

路径与阶段 2《应用页面说明》中的 43 个地址一致，
拆分应用时未作任何改动；路由名与注册表 ``core/pages.py``
中的 ``name`` 相同，通过命名空间 ``accounts`` 引用。
"""

from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("accounts/login/", views.login_view, name="login"),
    path("accounts/register/", views.register_view, name="register"),
    path("accounts/logout/", views.logout_view, name="logout"),
    path("enterprises/profile/", views.enterprise_profile_view,
         name="enterprise_profile"),
    path("enterprises/verification/", views.enterprise_verification_view,
         name="enterprise_verification"),
    path("enterprises/members/", views.enterprise_members_view,
         name="enterprise_members"),
    path("enterprises/invitations/", views.enterprise_invitations_view,
         name="enterprise_invitations"),
]
