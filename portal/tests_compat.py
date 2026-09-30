# -*- coding: utf-8 -*-
"""Тесты совместимости с Python 3.14 (``portal/compat.py``).

Копирование контекста шаблона — приём, на котором стоит отрисовка почти
любой страницы. Django 4.2 выполняет его через ``copy(super())``, и на
Python 3.14 это перестало работать: панель открывалась на главной, но
любой переход отвечал ошибкой 500.

Здесь проверяется не номер версии, а само свойство: контекст должен
копироваться, а обход — включаться только тогда, когда родная реализация
действительно сломана.
"""

import copy
import sys

from django.template.context import BaseContext, Context
from django.test import SimpleTestCase

from portal import compat


class ContextCopyTest(SimpleTestCase):
    """Копия контекста — основа отрисовки; она обязана работать."""

    def test_base_context_is_copyable(self):
        """Копия контекста создаётся и содержит отдельный список ``dicts``."""
        original = BaseContext()
        duplicate = copy.copy(original)
        self.assertIsInstance(duplicate, BaseContext)
        self.assertIsNot(duplicate, original)
        self.assertIsNot(duplicate.dicts, original.dicts)
        self.assertEqual(duplicate.dicts, original.dicts)

    def test_context_is_copyable(self):
        """Подкласс ``Context`` копируется через ``super().__copy__()``.

        Именно этот путь (``django/template/context.py``, ``Context``)
        падал в исходном отчёте об ошибке. Копия поверхностная, поэтому
        содержимое сохраняется, а список ``dicts`` — новый.
        """
        original = Context({"key": "value"})
        duplicate = copy.copy(original)
        self.assertIsInstance(duplicate, Context)
        self.assertEqual(duplicate["key"], "value")
        self.assertIsNot(duplicate.dicts, original.dicts)

    def test_copy_shares_inner_dicts(self):
        """Копирование поверхностное: список новый, словари — те же."""
        original = BaseContext()
        duplicate = copy.copy(original)
        if original.dicts:
            self.assertIs(duplicate.dicts[0], original.dicts[0])


class CompatPatchTest(SimpleTestCase):
    """Сам обход: включается по необходимости и не срабатывает дважды."""

    def setUp(self):
        self._original = BaseContext.__copy__
        self.addCleanup(setattr, BaseContext, "__copy__", self._original)

    def test_patch_is_idempotent(self):
        """Повторный вызов не переписывает реализацию заново."""
        self.assertFalse(compat.patch_template_context())

    def test_native_copy_is_kept_when_it_works(self):
        """Если родная реализация работает — обход не включается."""

        def native(self):
            duplicate = self.__class__.__new__(self.__class__)
            duplicate.__dict__.update(self.__dict__)
            duplicate.dicts = self.dicts[:]
            return duplicate

        BaseContext.__copy__ = native
        self.assertFalse(compat.patch_template_context())
        self.assertIs(BaseContext.__copy__, native)

    def test_patch_replaces_broken_copy(self):
        """Если копирование сломано — реализация подменяется рабочей."""
        if sys.version_info < compat.BROKEN_FROM:
            self.skipTest("на этой версии Python обход выключен по версии")

        def broken(self):
            raise AttributeError(
                "'super' object has no attribute 'dicts' and "
                "no __dict__ for setting new attributes")

        BaseContext.__copy__ = broken
        self.assertTrue(compat.patch_template_context())
        self.assertIs(BaseContext.__copy__, compat._copy_context)
        # И после подмены копия действительно создаётся.
        self.assertIsInstance(copy.copy(BaseContext()), BaseContext)

    def test_version_gate_wins_below_broken_from(self):
        """Ниже ``BROKEN_FROM`` обход не включается, даже если копия сломана.

        На 3.12 и 3.13 родная реализация работает, поэтому вмешиваться
        нельзя — поведение Django должно остаться нетронутым.
        """
        if sys.version_info >= compat.BROKEN_FROM:
            self.skipTest("на этой версии Python обход как раз и нужен")

        def broken(self):
            raise AttributeError("broken")

        BaseContext.__copy__ = broken
        self.assertFalse(compat.patch_template_context())
        self.assertIs(BaseContext.__copy__, broken)

    def test_marker_records_the_substitution(self):
        """Признак ``_portal_compat`` отличает подмену от родной функции."""
        if sys.version_info < compat.BROKEN_FROM:
            self.skipTest("обход не нужен на этой версии Python")
        if BaseContext.__copy__ is not compat._copy_context:
            self.skipTest("родная реализация работает — подмены нет")
        self.assertTrue(getattr(BaseContext.__copy__, "_portal_compat", False))

    def test_patched_copy_matches_original_semantics(self):
        """Подмена повторяет поведение исходной реализации."""
        source = BaseContext()
        source["a"] = 1
        source.push()
        source["b"] = 2
        duplicate = compat._copy_context(source)
        self.assertIsNot(duplicate, source)
        self.assertEqual(duplicate.dicts, source.dicts)
        self.assertIsNot(duplicate.dicts, source.dicts)
