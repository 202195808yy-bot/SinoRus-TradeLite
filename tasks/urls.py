# -*- coding: utf-8 -*-
"""任务与提醒 的路由（M8）。

路径与阶段 2《应用页面说明》中的 43 个地址一致，
拆分应用时未作任何改动；路由名与注册表 ``core/pages.py``
中的 ``name`` 相同，通过命名空间 ``tasks`` 引用。
"""

from django.urls import path

from . import views

app_name = "tasks"

urlpatterns = [
    path("tasks/", views.task_board_view, name="task_board"),
    path("tasks/<int:pk>/", views.task_detail_view, name="task_detail"),
    path("notifications/settings/", views.notification_settings_view,
         name="notification_settings"),
]
