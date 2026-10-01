# -*- coding: utf-8 -*-
"""冒烟测试：通过 Django 测试客户端请求应用的每个页面。

检查路由、视图与模板能否协同工作。
运行：  python tools/smoke_test.py
"""

import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tradehub.settings")
django.setup()

from django.test import Client  # noqa: E402
from django.test.utils import setup_test_environment  # noqa: E402

from core.pages import PAGES  # noqa: E402


def main():
    # 在 ALLOWED_HOSTS 中注册 “testserver” 主机
    setup_test_environment()
    client = Client()
    ok, failed = 0, []
    print("=" * 72)
    print("ДЫМОВОЙ ТЕСТ СТРАНИЦ")
    print("=" * 72)
    for page in PAGES:
        if page["view"] is None:
            url = "/" + page["path"]
        elif "<int:pk>" in page["path"]:
            url = "/" + page["path"].replace("<int:pk>", "1")
        else:
            url = "/" + page["path"]
        try:
            response = client.get(url)
        except Exception as exc:                     # noqa: BLE001
            failed.append((url, page["name"], repr(exc)))
            print(f"  [ИСКЛЮЧЕНИЕ] {url:<38} {exc}")
            continue
        status = response.status_code
        # 对于会重定向的页面（退出、管理后台），302 是允许的
        good = status in (200, 302)
        flag = "OK " if good else "!! "
        if good:
            ok += 1
        else:
            failed.append((url, page["name"], status))
        print(f"  {flag} {status}  {url:<38} {page['ru']}")

    print()
    print(f"Успешно: {ok}   Ошибок: {len(failed)}")
    if failed:
        print("\nПРОБЛЕМНЫЕ СТРАНИЦЫ:")
        for url, name, info in failed:
            print(f"  {url}  ({name})  -> {info}")
        sys.exit(1)
    print("ДЫМОВОЙ ТЕСТ ПРОЙДЕН.")


if __name__ == "__main__":
    main()
