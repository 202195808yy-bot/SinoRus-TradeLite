# -*- coding: utf-8 -*-
"""与 Python 3.14 的兼容性测试（``core/compat.py``）。

测试是跨领域的符合性测试（路由、语言字典完整性、管理后台
元数据、Python 版本兼容），因此集中在内核的测试包里，
而不是按应用拆散——它们检查的正是各应用之间的**一致**。
"""
"""与 Python 3.14 的兼容性测试（``core/compat.py``）。

模板上下文的复制是几乎每个页面的渲染所依赖的操作。
Django 4.2 通过 ``copy(super())`` 完成它，而在
Python 3.14 上这失效了：面板能在首页打开，但
任何跳转都返回 500 错误。

这里检查的不是版本号，而是属性本身：上下文必须
可复制，而变通方案只在原生实现
确实损坏时才启用。
"""

import copy
import sys

from django.template.context import BaseContext, Context
from django.test import SimpleTestCase

from core import compat


class ContextCopyTest(SimpleTestCase):
    """上下文副本是渲染的基础；它必须可用。"""

    def test_base_context_is_copyable(self):
        """上下文副本被创建并包含独立的 ``dicts`` 列表。"""
        original = BaseContext()
        duplicate = copy.copy(original)
        self.assertIsInstance(duplicate, BaseContext)
        self.assertIsNot(duplicate, original)
        self.assertIsNot(duplicate.dicts, original.dicts)
        self.assertEqual(duplicate.dicts, original.dicts)

    def test_context_is_copyable(self):
        """``Context`` 子类通过 ``super().__copy__()`` 复制。

        正是这条路径（``django/template/context.py``、``Context``）
        在最初的错误报告中崩溃。副本是浅层的，因此
        内容得以保留，而 ``dicts`` 列表是新的。
        """
        original = Context({"key": "value"})
        duplicate = copy.copy(original)
        self.assertIsInstance(duplicate, Context)
        self.assertEqual(duplicate["key"], "value")
        self.assertIsNot(duplicate.dicts, original.dicts)

    def test_copy_shares_inner_dicts(self):
        """复制是浅层的：列表是新的，字典不变。"""
        original = BaseContext()
        duplicate = copy.copy(original)
        if original.dicts:
            self.assertIs(duplicate.dicts[0], original.dicts[0])


class CompatPatchTest(SimpleTestCase):
    """变通本身：按需启用且不会重复生效。"""

    def setUp(self):
        self._original = BaseContext.__copy__
        self.addCleanup(setattr, BaseContext, "__copy__", self._original)

    def test_patch_is_idempotent(self):
        """重复调用不会重新改写实现。"""
        self.assertFalse(compat.patch_template_context())

    def test_native_copy_is_kept_when_it_works(self):
        """若原生实现正常 — 不启用变通。"""

        def native(self):
            duplicate = self.__class__.__new__(self.__class__)
            duplicate.__dict__.update(self.__dict__)
            duplicate.dicts = self.dicts[:]
            return duplicate

        BaseContext.__copy__ = native
        self.assertFalse(compat.patch_template_context())
        self.assertIs(BaseContext.__copy__, native)

    def test_patch_replaces_broken_copy(self):
        """若复制已损坏 — 实现被替换为可用的版本。"""
        if sys.version_info < compat.BROKEN_FROM:
            self.skipTest("на этой версии Python обход выключен по версии")

        def broken(self):
            raise AttributeError(
                "'super' object has no attribute 'dicts' and "
                "no __dict__ for setting new attributes")

        BaseContext.__copy__ = broken
        self.assertTrue(compat.patch_template_context())
        self.assertIs(BaseContext.__copy__, compat._copy_context)
        # 且在替换之后副本确实会被创建。
        self.assertIsInstance(copy.copy(BaseContext()), BaseContext)

    def test_version_gate_wins_below_broken_from(self):
        """版本低于 ``BROKEN_FROM`` 时，即使副本已损坏也不启用变通。

        在 3.12 和 3.13 上原生实现正常，因此不得干预 —
        Django 的行为必须保持原样。
        """
        if sys.version_info >= compat.BROKEN_FROM:
            self.skipTest("на этой версии Python обход как раз и нужен")

        def broken(self):
            raise AttributeError("broken")

        BaseContext.__copy__ = broken
        self.assertFalse(compat.patch_template_context())
        self.assertIs(BaseContext.__copy__, broken)

    def test_marker_records_the_substitution(self):
        """标志 ``_core_compat`` 用于区分替换版与原生函数。"""
        if sys.version_info < compat.BROKEN_FROM:
            self.skipTest("обход не нужен на этой версии Python")
        if BaseContext.__copy__ is not compat._copy_context:
            self.skipTest("родная реализация работает — подмены нет")
        self.assertTrue(getattr(BaseContext.__copy__, "_core_compat", False))

    def test_patched_copy_matches_original_semantics(self):
        """替换版复现原始实现的行为。"""
        source = BaseContext()
        source["a"] = 1
        source.push()
        source["b"] = 2
        duplicate = compat._copy_context(source)
        self.assertIsNot(duplicate, source)
        self.assertEqual(duplicate.dicts, source.dicts)
        self.assertIsNot(duplicate.dicts, source.dicts)
