# -*- coding: utf-8 -*-
"""TradeHub 项目的根路由。

项目 = 全局配置 + 应用集合。每个应用在自己的 ``urls.py`` 里
声明路由（含 ``app_name`` 命名空间），这里按「内核 -> 领域」
的顺序逐个 ``include()``。

URL 路径与阶段 2《应用页面说明》中的 43 个地址完全一致；
拆分应用时只改变了命名空间（``portal:`` -> ``<app>:``），
路径本身一个都没有动。
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),

    # --- 内核：主页、关于、帮助、语言切换 -------------------------
    path("", include("core.urls")),

    # --- M0 登录/注册 + M1 企业与账号 -----------------------------
    path("", include("accounts.urls")),

    # --- M2 商品 --------------------------------------------------
    path("", include("catalog.urls")),

    # --- M3 询价报价 + M4 订单 ------------------------------------
    path("", include("trading.urls")),

    # --- M5 物流与口岸 --------------------------------------------
    path("", include("logistics.urls")),

    # --- M6 单证与合规 --------------------------------------------
    path("", include("documents.urls")),

    # --- M7 双语沟通 ----------------------------------------------
    path("", include("messaging.urls")),

    # --- M8 任务与提醒 --------------------------------------------
    path("", include("tasks.urls")),

    # --- M9 数据看板 ----------------------------------------------
    path("", include("analytics.urls")),

    # --- M10 结算与对账 -------------------------------------------
    path("", include("billing.urls")),

    # --- M11 系统管理 ---------------------------------------------
    path("", include("system.urls")),
]
