# -*- coding: utf-8 -*-
"""管理后台的站点级设置。

拆分后每个应用在自己的 ``admin.py`` 里注册自己的模型；
这里只保留与具体模型无关的站点文案。面板站点类本身是
``core/admin_site.TradeHubAdminSite``，通过 ``core/apps.py``
中的 ``default_site`` 接入，主页的分组逻辑在那里。
"""

from django.contrib import admin

from .admin_i18n import LazyRu

admin.site.site_header = LazyRu("Администрирование TradeHub")
admin.site.site_title = "TradeHub"
#: 主页标题。译文在 ``ADMIN_LABELS`` (``admin_labels.py``) 中。
admin.site.index_title = LazyRu("Обзор данных")
