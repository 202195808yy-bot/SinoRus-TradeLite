# -*- coding: utf-8 -*-
"""检查页面与模型（<app>/datasets.py）的对接情况。

显示哪些页面从模型获取数据、哪些仍停留在
原型状态，并核对提供器注册表与页面注册表的
一致性。没有页面的提供器，以及带参数
pk 而没有提供器的页面，均视为错误。

运行：  python tools/check_data.py
"""

import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tradehub.settings")
django.setup()

from core.datasets import PAGE_DATA, coverage            # noqa: E402
from core.pages import PAGE_BY_NAME, PAGES               # noqa: E402


def main():
    print("=" * 72)
    print("ПОДКЛЮЧЕНИЕ СТРАНИЦ К МОДЕЛЯМ (<app>/datasets.py)")
    print("=" * 72)

    errors = []
    current_module = None
    for page in PAGES:
        if page["module"] != current_module:
            current_module = page["module"]
            print(f"\n  --- {current_module} ---")
        name = page["name"]
        has_pk = bool(page["params"])
        if name in PAGE_DATA:
            mark, state = "+", "данные моделей"
        elif page["view"] is None:
            mark, state = "·", "вне приложения (admin)"
        else:
            mark, state = "-", "прототип"
        print(f"  {mark} {name:<24} pk={'да ' if has_pk else 'нет'}  {state}")

    # --- 注册表核对
    unknown = sorted(set(PAGE_DATA) - set(PAGE_BY_NAME))
    if unknown:
        errors.append(f"провайдеры без страницы в реестре: {unknown}")

    for page in PAGES:
        if page["params"] and page["name"] not in PAGE_DATA \
                and page["view"] is not None:
            errors.append(
                f"страница с параметром pk не подключена: {page['name']}")

    wired, proto = coverage()
    print()
    print("=" * 72)
    print(f"Страниц всего:              {len(PAGES)}")
    print(f"  с данными моделей:        {len(wired)}")
    print(f"  прототипы:                {len(proto)} {proto}")
    print("=" * 72)

    if errors:
        for e in errors:
            print("  [ОШИБКА]", e)
        print(f"\nПРОВЕРКА НЕ ПРОЙДЕНА: ошибок {len(errors)}")
        sys.exit(1)

    print("ПРОВЕРКА ПРОЙДЕНА: реестр провайдеров согласован с реестром "
          "страниц.")


if __name__ == "__main__":
    main()
