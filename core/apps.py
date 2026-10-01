# -*- coding: utf-8 -*-
"""平台内核的应用配置。

这里是**整个项目**的启动钩子，因为内核先于其他应用加载：

* ``AdminConfig.default_site`` —— 替换管理后台站点类。该值必须
  在 ``django.setup()`` 之前设置：``django.contrib.admin.sites.site``
  是惰性对象，它在第一次访问时才从 admin 的应用配置里读取
  ``default_site``，而第一次访问发生在
  ``AdminConfig.ready()`` -> ``autodiscover()``——那时注册表
  已经填满了模型。因此这里在**模块级**赋值。
* ``ready()`` —— 打开管理后台标签的翻译
  （``core/admin_i18n.py``）以及 Python 3.14 的兼容绕过
  （``core/compat.py``）。
"""

from django.apps import AppConfig
from django.contrib.admin import apps as admin_apps

# 用「模块.类」而不是 `from ... import AdminConfig`：
# ``AppConfig.create()`` 会用 ``inspect.getmembers`` 在本模块里找
# AppConfig 子类，若把 ``AdminConfig`` 直接引入命名空间，它会被
# 误认为本应用的配置类（两者 label 都是 admin）而报
# 「Application labels aren't unique」。
admin_apps.AdminConfig.default_site = "core.admin_site.TradeHubAdminSite"


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Ядро платформы"

    def ready(self):
        """启用管理面板标签的翻译与 Python 3.14 兼容绕过。

        应用、模型和字段的标签由面板取自 ORM 元数据，
        并以俄语书写。这里将它们包装为惰性翻译
        （``core/admin_i18n.py``），因此面板会与其余界面一起切换。
        在方法内部导入——因为加载 ``apps.py`` 时
        应用注册表尚未就绪。
        """
        from .admin_i18n import localize
        from .compat import patch_template_context

        patch_template_context()
        localize()
