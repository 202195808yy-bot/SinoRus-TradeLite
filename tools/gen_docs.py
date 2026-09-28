# -*- coding: utf-8 -*-
"""Генерация docs/pages.{ru,zh,en}.md из реестра страниц portal/pages.py.

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

from portal.pages import (  # noqa: E402
    LANGS, MODULES, PAGES, content_of, module_name, pages_of, params_of,
    purpose_of, title_of,
)

DOCS = os.path.join(ROOT, "docs")

ACCESS = {
    "ru": {
        "public": "Общедоступная",
        "auth": "Требуется вход",
        "role": "Ограничено ролью",
    },
    "zh": {
        "public": "公开",
        "auth": "需登录",
        "role": "限角色",
    },
    "en": {
        "public": "Public",
        "auth": "Sign-in required",
        "role": "Role-restricted",
    },
}

L = {
    "ru": {
        "title": "# Перечень страниц приложения",
        "intro": [
            "Курсовой проект по дисциплине «Разработка веб-приложений "
            "на Python».",
            "",
            "Приложение: «Легковесная платформа совместной работы для "
            "трансграничной торговли России и Китая» — веб-клиент.",
        ],
        "note": "> Файл сгенерирован автоматически из `portal/pages.py` "
                "командой `python tools/gen_docs.py`. "
                "Не редактируйте вручную.",
        "summary": "## Сводка",
        "sum_head": ["Показатель", "Значение"],
        "sum_rows": ["Всего страниц", "Модулей",
                     "Страниц с собственным маршрутом Django",
                     "Страниц, обслуживаемых `django.contrib.admin`"],
        "routes": "## Маршруты по модулям",
        "routes_head": ["№", "Страница", "Адрес (URL)", "Имя маршрута",
                        "Представление", "Доступ"],
        "descr": "## Описание страниц",
        "lbl_route": "Имя маршрута",
        "lbl_view": "Представление",
        "lbl_access": "Режим доступа",
        "lbl_params": "Параметры маршрута",
        "lbl_purpose": "Назначение",
        "lbl_content": "Основное содержание",
        "admin_view": "— (django.contrib.admin)",
        "sep": ":",
    },
    "zh": {
        "title": "# 应用页面列表",
        "intro": [
            "《Python Web 应用开发》课程设计。",
            "",
            "应用：「中俄跨境贸易轻量协同平台」——Web 客户端。",
        ],
        "note": "> 本文件由 `portal/pages.py` 自动生成"
                "（`python tools/gen_docs.py`），请勿手工编辑。",
        "summary": "## 概览",
        "sum_head": ["指标", "数值"],
        "sum_rows": ["页面总数", "模块数", "有独立 Django 路由的页面",
                     "由 `django.contrib.admin` 提供的页面"],
        "routes": "## 各模块的页面与地址",
        "routes_head": ["序号", "页面", "地址（URL）", "路由名",
                        "视图", "访问权限"],
        "descr": "## 页面描述",
        "lbl_route": "路由名",
        "lbl_view": "视图",
        "lbl_access": "访问权限",
        "lbl_params": "路由参数",
        "lbl_purpose": "用途",
        "lbl_content": "主要内容",
        "admin_view": "—（django.contrib.admin）",
        "sep": "：",
    },
    "en": {
        "title": "# Application page list",
        "intro": [
            "Course project for the discipline “Web application "
            "development in Python”.",
            "",
            "Application: “Lightweight collaboration platform for "
            "Russia–China cross-border trade” — web client.",
        ],
        "note": "> Generated automatically from `portal/pages.py` by "
                "`python tools/gen_docs.py`. Do not edit by hand.",
        "summary": "## Summary",
        "sum_head": ["Metric", "Value"],
        "sum_rows": ["Total pages", "Modules",
                     "Pages with their own Django route",
                     "Pages served by `django.contrib.admin`"],
        "routes": "## Routes by module",
        "routes_head": ["No.", "Page", "Address (URL)", "Route name",
                        "View", "Access"],
        "descr": "## Page descriptions",
        "lbl_route": "Route name",
        "lbl_view": "View",
        "lbl_access": "Access",
        "lbl_params": "Route parameters",
        "lbl_purpose": "Purpose",
        "lbl_content": "Main content",
        "admin_view": "— (django.contrib.admin)",
        "sep": ":",
    },
}


def render(lang):
    t = L[lang]
    own = len([p for p in PAGES if p["view"]])
    admin = len(PAGES) - own

    out = [t["title"], ""]
    out += t["intro"]
    out += ["", t["note"], "", t["summary"], "",
            f"| {t['sum_head'][0]} | {t['sum_head'][1]} |",
            "|---|---|",
            f"| {t['sum_rows'][0]} | {len(PAGES)} |",
            f"| {t['sum_rows'][1]} | {len(MODULES)} |",
            f"| {t['sum_rows'][2]} | {own} |",
            f"| {t['sum_rows'][3]} | {admin} |",
            "", t["routes"], ""]

    for code, *_ in MODULES:
        out.append(f"### {code}. {module_name(code, lang)}")
        out.append("")
        out.append("| " + " | ".join(t["routes_head"]) + " |")
        out.append("|---|---|---|---|---|---|")
        for i, p in enumerate(pages_of(code), 1):
            view = f"`{p['view']}`" if p["view"] else t["admin_view"]
            out.append(
                f"| {i} | {title_of(p, lang)} | `/{p['path']}` | "
                f"`{p['name']}` | {view} | {ACCESS[lang][p['access']]} |"
            )
        out.append("")

    out += [t["descr"], ""]
    for code, *_ in MODULES:
        out.append(f"### {code}. {module_name(code, lang)}")
        out.append("")
        for p in pages_of(code):
            out.append(f"#### `/{p['path']}` — {title_of(p, lang)}")
            out.append("")
            s = t["sep"]
            out.append(f"- **{t['lbl_route']}{s}** `{p['name']}`")
            if p["view"]:
                out.append(f"- **{t['lbl_view']}{s}** "
                           f"`portal.views.{p['view']}`")
            else:
                out.append(f"- **{t['lbl_view']}{s}** `django.contrib.admin`")
            out.append(f"- **{t['lbl_access']}{s}** "
                       f"{ACCESS[lang][p['access']]}")
            params = params_of(p, lang)
            if params:
                out.append(f"- **{t['lbl_params']}{s}** {params}")
            out.append(f"- **{t['lbl_purpose']}{s}** {purpose_of(p, lang)}")
            out.append(f"- **{t['lbl_content']}{s}** {content_of(p, lang)}")
            out.append("")

    return "\n".join(out)


def main():
    os.makedirs(DOCS, exist_ok=True)
    for lang in LANGS:
        path = os.path.join(DOCS, f"pages.{lang}.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(render(lang))
        print(f"written: {path}")
    print(f"pages: {len(PAGES)}, modules: {len(MODULES)}, langs: {len(LANGS)}")


if __name__ == "__main__":
    main()
