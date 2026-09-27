# -*- coding: utf-8 -*-
"""Генерация docs/pages.md из реестра страниц portal/pages.py.

Единый источник данных гарантирует, что перечень страниц в репозитории
и в документе «Описание страниц приложения» не расходятся.
Запуск:  python tools/gen_docs.py
"""

import os
import sys

import django

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tradehub.settings")
django.setup()

from portal.pages import MODULES, PAGES, pages_of  # noqa: E402

OUT = os.path.join(ROOT, "docs", "pages.md")

ACCESS_RU = {
    "public": "Общедоступная",
    "auth": "Требуется вход",
    "role": "Ограничено ролью",
}

HEAD = """# Перечень страниц приложения

Курсовой проект по дисциплине «Разработка веб-приложений на Python».

Приложение: «Легковесная платформа совместной работы для трансграничной
торговли России и Китая» — веб-клиент.

> Файл сгенерирован автоматически из `portal/pages.py` командой
> `python tools/gen_docs.py`. Не редактируйте вручную.

## Сводка

| Показатель | Значение |
|---|---|
| Всего страниц | {total} |
| Модулей | {modules} |
| Страниц с собственным маршрутом Django | {own} |
| Страниц, обслуживаемых `django.contrib.admin` | {admin} |

## Маршруты по модулям
"""


def main():
    lines = [HEAD.format(
        total=len(PAGES),
        modules=len(MODULES),
        own=len([p for p in PAGES if p["view"]]),
        admin=len([p for p in PAGES if not p["view"]]),
    )]

    for code, ru, zh in MODULES:
        lines.append(f"\n### {code}. {ru} / {zh}\n")
        lines.append("| № | Страница | Адрес (URL) | Имя маршрута | Представление | Доступ |")
        lines.append("|---|---|---|---|---|---|")
        for i, p in enumerate(pages_of(code), 1):
            view = f"`{p['view']}`" if p["view"] else "— (django.contrib.admin)"
            lines.append(
                f"| {i} | {p['ru']} / {p['zh']} | `/{p['path']}` | "
                f"`{p['name']}` | {view} | {ACCESS_RU[p['access']]} |"
            )

    lines.append("\n## Описание страниц\n")
    for code, ru, zh in MODULES:
        lines.append(f"\n### {code}. {ru} / {zh}\n")
        for p in pages_of(code):
            lines.append(f"#### `/{p['path']}` — {p['ru']} / {p['zh']}\n")
            lines.append(f"- **Имя маршрута:** `{p['name']}`")
            if p["view"]:
                lines.append(f"- **Представление:** `portal.views.{p['view']}`")
            else:
                lines.append("- **Представление:** `django.contrib.admin`")
            lines.append(f"- **Режим доступа:** {ACCESS_RU[p['access']]}")
            if p["params"]:
                lines.append(f"- **Параметры маршрута:** {p['params']}")
            lines.append(f"- **Назначение:** {p['purpose']}")
            lines.append(f"- **Основное содержание:** {p['content']}")
            lines.append("")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"written: {OUT}")
    print(f"pages: {len(PAGES)}")


if __name__ == "__main__":
    main()
