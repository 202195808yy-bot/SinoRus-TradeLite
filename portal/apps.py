# -*- coding: utf-8 -*-
"""portal 应用配置。"""

from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig

#: 面板站点类。``django.contrib.admin.sites.site`` 是惰性的
#: 对象：它从 admin 应用配置中读取 ``default_site``
#: 是在第一次访问时，而第一次访问发生在
#: ``AdminConfig.ready()`` -> ``autodiscover()``。因此该值必须
#: 在 ``django.setup()`` 之前设置——也就是模块级别，而不是在
#: ``ready()`` 里：到那时注册表已经填满了模型。
AdminConfig.default_site = "portal.admin_site.TradeHubAdminSite"


class PortalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "portal"
    verbose_name = "Портал трансграничной торговли"

    def ready(self):
        """启用管理面板标签的翻译。

        应用、模型和字段的标签由面板取自 ORM 元数据，
        并以俄语书写。这里将它们包装为惰性翻译
        （``portal/admin_i18n.py``），因此面板会与其余界面一起切换。
        在方法内部导入——因为加载 ``apps.py`` 时
        应用注册表尚未就绪。

        这里同时启用针对 Python 3.14 的绕过方案：Django 4.2 通过
        ``copy(super())`` 复制模板上下文，而在 3.14 上这不再
        有效——除主页外的所有面板页面都会崩溃
        （``portal/compat.py``）。
        """
        from .admin_i18n import localize
        from .compat import patch_template_context

        patch_template_context()
        localize()
