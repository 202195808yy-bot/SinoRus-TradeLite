# -*- coding: utf-8 -*-
"""Маршруты приложения portal.

Маршруты сгруппированы по функциональным модулям M0..M11.
Полное описание страниц приведено в docs/pages.{ru,zh,en}.md и в документе
«Описание страниц приложения».
"""

from django.urls import path

from . import views

app_name = "portal"

urlpatterns = [
    # ------------------------------------------------- переключение языка
    # Отдельный маршрут, а не ?lang=: в административной панели неизвестный
    # параметр запроса трактуется как фильтр списка и даёт лишний редирект.
    path("lang/<str:code>/", views.set_language_view, name="set_language"),

    # ---------------------------------------------------------- M0 公共页面
    path("", views.index_view, name="index"),
    path("about/", views.about_view, name="about"),
    path("help/", views.help_view, name="help"),
    path("accounts/login/", views.login_view, name="login"),
    path("accounts/register/", views.register_view, name="register"),
    path("accounts/logout/", views.logout_view, name="logout"),

    # ------------------------------------------------- M1 企业与账号
    path("enterprises/profile/", views.enterprise_profile_view,
         name="enterprise_profile"),
    path("enterprises/verification/", views.enterprise_verification_view,
         name="enterprise_verification"),
    path("enterprises/members/", views.enterprise_members_view,
         name="enterprise_members"),
    path("enterprises/invitations/", views.enterprise_invitations_view,
         name="enterprise_invitations"),

    # ---------------------------------------------------------- M2 商品
    path("goods/", views.goods_list_view, name="goods_list"),
    path("goods/<int:pk>/", views.goods_detail_view, name="goods_detail"),
    path("goods/new/", views.goods_form_view, name="goods_form"),

    # ------------------------------------------------------ M3 询价与报价
    path("rfqs/", views.rfq_list_view, name="rfq_list"),
    path("rfqs/new/", views.rfq_create_view, name="rfq_create"),
    path("rfqs/<int:pk>/", views.rfq_detail_view, name="rfq_detail"),
    path("quotes/", views.quote_list_view, name="quote_list"),
    path("quotes/<int:pk>/", views.quote_detail_view, name="quote_detail"),

    # ---------------------------------------------------------- M4 订单
    path("orders/", views.order_list_view, name="order_list"),
    path("orders/<int:pk>/", views.order_detail_view, name="order_detail"),
    path("orders/<int:pk>/milestones/", views.order_milestones_view,
         name="order_milestones"),
    path("orders/<int:pk>/changes/", views.order_changes_view,
         name="order_changes"),

    # ------------------------------------------------------ M5 物流与口岸
    path("shipments/", views.shipment_list_view, name="shipment_list"),
    path("shipments/<int:pk>/", views.shipment_detail_view,
         name="shipment_detail"),
    path("exceptions/", views.exception_list_view, name="exception_list"),
    path("exceptions/new/", views.exception_create_view,
         name="exception_create"),

    # ------------------------------------------------------ M6 单证与合规
    path("documents/", views.documents_list_view, name="documents_list"),
    path("documents/upload/", views.documents_upload_view,
         name="documents_upload"),
    path("certificates/", views.certificates_list_view,
         name="certificates_list"),
    path("compliance/self-check/", views.compliance_check_view,
         name="compliance_check"),

    # ------------------------------------------------------ M7 双语沟通
    path("messages/", views.message_list_view, name="message_list"),
    path("messages/<int:pk>/", views.message_detail_view,
         name="message_detail"),

    # ------------------------------------------------------ M8 任务与提醒
    path("tasks/", views.task_board_view, name="task_board"),
    path("tasks/<int:pk>/", views.task_detail_view, name="task_detail"),
    path("notifications/settings/", views.notification_settings_view,
         name="notification_settings"),

    # ---------------------------------------------------------- M9 数据看板
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("dashboard/logistics/", views.dashboard_logistics_view,
         name="dashboard_logistics"),
    path("dashboard/compliance/", views.dashboard_compliance_view,
         name="dashboard_compliance"),

    # ------------------------------------------------------ M10 结算与对账
    path("statements/", views.statement_list_view, name="statement_list"),
    path("statements/<int:pk>/", views.statement_detail_view,
         name="statement_detail"),

    # ------------------------------------------------------ M11 系统管理
    path("system/audit-logs/", views.audit_log_list_view,
         name="audit_log_list"),
    path("system/dictionaries/", views.dictionary_list_view,
         name="dictionary_list"),
]
