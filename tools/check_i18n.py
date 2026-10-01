# -*- coding: utf-8 -*-
"""检查页面注册表 core/pages.py 翻译的完整性。

检查每页的名称、用途与内容是否按 `pages.LANGS` 中的
所有语言填写，以及带参数的页面是否填写了
路由参数说明。

另外还会对可疑的字母表混用发出警告：
俄语或英语文本中出现汉字。

运行：  python tools/check_i18n.py
"""

import os
import re
import sys

import django

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tradehub.settings")
django.setup()

from core.pages import LANGS, MODULES, PAGES  # noqa: E402

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

        # 字母表检查：汉字只允许出现在中文字段中
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
