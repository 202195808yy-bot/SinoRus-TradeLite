# -*- coding: utf-8 -*-
"""Дымовой тест: запрос каждой страницы приложения через тестовый клиент Django.

Проверяет, что маршрут, представление и шаблон работают совместно.
Запуск:  python tools/smoke_test.py
"""

import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tradehub.settings")
django.setup()

from django.test import Client  # noqa: E402
from django.test.utils import setup_test_environment  # noqa: E402

from portal.pages import PAGES  # noqa: E402


def main():
    # регистрирует хост «testserver» в ALLOWED_HOSTS
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
        # 302 допустим для страниц, которые перенаправляют (выход, админ-панель)
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
