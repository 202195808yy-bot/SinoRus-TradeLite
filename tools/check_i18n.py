# -*- coding: utf-8 -*-
"""Проверка полноты переводов реестра страниц portal/pages.py.

Контролирует, что для каждой страницы заполнены названия, назначение и
содержание на всех языках из `pages.LANGS`, а описания параметров маршрута
заполнены для страниц с параметрами.

Дополнительно предупреждает о подозрительном смешении алфавитов:
иероглифы в русском или английском тексте.

Запуск:  python tools/check_i18n.py
"""

import os
import re
import sys

import django

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tradehub.settings")
django.setup()

from portal.pages import LANGS, MODULES, PAGES  # noqa: E402

CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
CYRILLIC = re.compile(r"[\u0400-\u04ff]")


def main():
    problems = []
    warnings = []

    for code, *names in MODULES:
        if len(names) != len(LANGS) or any(not n for n in names):
            problems.append(f"модуль {code}: не заполнены названия "
                            f"на всех языках")

    for p in PAGES:
        for lang in LANGS:
            for field in ("", "purpose_", "content_"):
                key = field + lang
                if not p.get(key):
                    problems.append(f"{p['name']}: пустое поле «{key}»")
        if p["params"]:
            for lang in LANGS:
                if not p["params"].get(lang):
                    problems.append(
                        f"{p['name']}: пустые параметры маршрута ({lang})")

        # алфавитный контроль: иероглифы допустимы только в китайских полях
        for lang in ("ru", "en"):
            for field in ("purpose_", "content_"):
                text = p.get(field + lang, "")
                if CJK.search(text):
                    warnings.append(
                        f"{p['name']}.{field}{lang}: иероглифы в тексте "
                        f"на «{lang}»")

    for w in warnings:
        print(f"  [warn] {w}")
    for e in problems:
        print(f"  [FAIL] {e}")

    print(f"страниц: {len(PAGES)}, языков: {len(LANGS)}, "
          f"модулей: {len(MODULES)}")
    if problems:
        print(f"ПРОВЕРКА НЕ ПРОЙДЕНА: {len(problems)} проблем.")
        sys.exit(1)
    print(f"ПРОВЕРКА ПРОЙДЕНА: переводы заполнены полностью"
          f"{f', предупреждений: {len(warnings)}' if warnings else ''}.")


if __name__ == "__main__":
    main()
