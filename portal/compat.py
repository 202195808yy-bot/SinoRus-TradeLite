# -*- coding: utf-8 -*-
"""与 Python 3.14 的兼容性：模板上下文的复制。

``requirements.txt`` 固定使用 Django 4.2.30——该分支支持
Python 3.8–3.12（3.13 在 Django 5.1 中出现，3.14 在 5.2 中）。但项目
也会在更新的版本上运行：虚拟环境 ``.venv``
基于 Python 3.14 搭建。

这时模板上下文的复制就会出问题。Django 4.2 的做法如下
（``django/template/context.py``）::

    def __copy__(self):
        duplicate = copy(super())
        duplicate.dicts = self.dicts[:]
        return duplicate

这一技巧基于如下事实：``super()`` 对象的属性读取
会委托给被包装的实例，因此 ``copy(super())`` 返回的是
**上下文**的副本，而不是 ``super`` 本身。在 Python 3.14 中这一行为
发生了变化：``copy(super())`` 返回 ``super`` 对象，随后
一行就会崩溃::

    AttributeError: 'super' object has no attribute 'dicts' and
    no __dict__ for setting new attributes

外在表现如下：面板主页可以打开（它不复制上下文），而
**任何跳转**——进入模型列表、进入卡片、进入
用户页面——都会返回 500 错误。测试集中 120 个测试有 40 个失败：
即所有在渲染模板时复制上下文的测试。

绕过方案在 ``PortalConfig.ready()`` 中启用，且仅在原生
实现确实损坏时才启用：在 Python 3.12 和 3.13 上它不会启用，
行为保持原生不变。
"""

import copy as _copy
import sys

#: 第一个 ``copy(super())`` 不再向被包装对象
#: 委托 ``__reduce_ex__`` 的 Python 版本。已在 3.12、3.13（正常）
#: 和 3.14（崩溃）上验证。
BROKEN_FROM = (3, 14)


def _copy_context(self):
    """不通过 ``super()`` 的上下文副本。

    复刻原始实现：新对象类型相同、
    ``__dict__`` 相同，``dicts`` 为独立列表。复制是浅层的——
    列表本身是新的，其中的字典不变。
    """
    duplicate = self.__class__.__new__(self.__class__)
    duplicate.__dict__.update(self.__dict__)
    duplicate.dicts = self.dicts[:]
    return duplicate


def patch_template_context():
    """若原生实现已损坏则启用绕过方案。已启用则返回 True。

    检测是真实进行的，而非按版本号判断：复制一个空上下文。
    如果复制成功——即使 Python 版本
    形式上是新的——也无需干预。
    """
    from django.template.context import BaseContext

    if sys.version_info < BROKEN_FROM:
        return False
    if getattr(BaseContext.__copy__, "_portal_compat", False):
        return False                      # 已启用
    try:
        _copy.copy(BaseContext())
    except Exception:                     # noqa: BLE001 —— 检查的正是这种情况
        pass
    else:
        return False                      # 原生实现正常工作
    _copy_context._portal_compat = True
    BaseContext.__copy__ = _copy_context
    return True
