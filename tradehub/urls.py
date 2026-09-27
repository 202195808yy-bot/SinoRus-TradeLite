"""
Корневая конфигурация маршрутов проекта tradehub.

Административная панель Django подключается по адресу /admin/,
все остальные маршруты передаются в приложение portal.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("portal.urls")),
]
