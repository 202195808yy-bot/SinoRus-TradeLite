# -*- coding: utf-8 -*-
"""路由检查：核对页面注册表与 Django 实际路由。

运行：  python tools/check_routes.py
"""

import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tradehub.settings")
django.setup()

from django.urls import NoReverseMatch, get_resolver, reverse  # noqa: E402

from portal.pages import PAGES  # noqa: E402


def walk(patterns, prefix=""):
    """遍历 URL 模板树并累积前缀。"""
    from django.urls.resolvers import URLPattern, URLResolver

    for p in patterns:
        if isinstance(p, URLResolver):
            yield from walk(p.url_patterns, prefix + str(p.pattern))
        elif isinstance(p, URLPattern):
            yield prefix + str(p.pattern), p.name


def main():
    print("=" * 72)
    print("МАРШРУТЫ, ЗАРЕГИСТРИРОВАННЫЕ В URLconf")
    print("=" * 72)
    routes = sorted(walk(get_resolver().url_patterns))
    for pattern, name in routes:
        print(f"  /{pattern:<40} name={name}")
    print(f"\nВсего маршрутов: {len(routes)}")

    print()
    print("=" * 72)
    print("СВЕРКА С РЕЕСТРОМ СТРАНИЦ (portal/pages.py)")
    print("=" * 72)
    errors = []
    for page in PAGES:
        if page["view"] is None:
            print(f"  {page['module']:<4} {'/' + page['path']:<38} "
                  f"{page['ru']} (django.contrib.admin)")
            continue
        try:
            if "<int:pk>" in page["path"]:
                url = reverse("portal:" + page["name"], kwargs={"pk": 1})
            else:
                url = reverse("portal:" + page["name"])
        except NoReverseMatch as exc:
            errors.append(f"  [ОШИБКА] {page['name']}: {exc}")
            continue
        print(f"  {page['module']:<4} {url:<38} {page['ru']}")

    declared = {p["name"] for p in PAGES if p["view"]}
    actual = {name for _, name in routes if name}
    missing = declared - actual

    if missing:
        errors.append(f"  [ОШИБКА] нет маршрута для страниц: {sorted(missing)}")

    print()
    if errors:
        print("\n".join(errors))
        print(f"\nПРОВЕРКА НЕ ПРОЙДЕНА: ошибок {len(errors)}")
        sys.exit(1)

    portal_routes = [r for r in routes
                     if not r[0].startswith("admin/")]
    print(f"Страниц в реестре: {len(PAGES)} "
          f"(из них с собственным маршрутом: {len(declared)})")
    print(f"Маршрутов приложения portal: {len(portal_routes)}")
    print("ПРОВЕРКА ПРОЙДЕНА: все страницы реестра имеют рабочий маршрут.")


if __name__ == "__main__":
    main()
