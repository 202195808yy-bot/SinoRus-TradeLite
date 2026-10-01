"""
tradehub 项目的根路由配置。

Django 管理后台挂载在 /admin/ 地址下，
其余路由全部交给 portal 应用。
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("portal.urls")),
]
