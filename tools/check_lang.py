# -*- coding: utf-8 -*-
"""检查翻译字典（core/labels.py、core/i18n.py）的完整性。

检查五项内容：

* 数据块标签 — 遍历 <app>/datasets.py 的全部提供器；
* 模型的 ``choices`` 枚举（状态、单证类型、计量
  单位）— 它们以值而非标签的形式进入单元格；
* 字典的值 — 国家、货币、单证类型、行业、
  商品类别；
* 管理后台的标签 — 应用、模型与字段的名称
  （``core/admin_labels.py``）；
* 自动创建的 M2M 关联模型的标签 — 它们不在 ``get_models()`` 中，
  但在删除确认页面上可见。

另外还检查界面外壳文本（portal/i18n.UI）。

未翻译的数据块标签、枚举、字典值、后台标签、
关联标签，以及外壳文本中的空翻译，
均视为错误。

运行：  python tools/check_lang.py
"""

import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tradehub.settings")
django.setup()

from core.i18n import LANGS, UI, tr                        # noqa: E402
from core.langcheck import (ENUM_SKIP, admin_labels, admin_overrides,  # noqa: E402
                              enum_labels, reference_values, scan,
                              through_labels, untranslated_admin_labels,
                              untranslated_enums, untranslated_reference_values,
                              untranslated_through_labels)

CYRILLIC = set("абвгдеёжзийклмнопрстуфхцчшщъыьэюя")


def main():
    print("=" * 72)
    print("ПОЛНОТА ПЕРЕВОДОВ ИНТЕРФЕЙСА (core/labels.py, core/i18n.py)")
    print("=" * 72)

    errors = []

    # --- 1. 数据块标签-------------------------------------
    found, missing, skipped = scan()
    print(f"\n  Подписей блоков собрано:      {len(found)}")
    print(f"  Переведено (portal/labels):   {len(found) - len(missing)}")
    if skipped:
        print(f"  Провайдеров без данных:       {len(skipped)}")
        for name in skipped:
            print(f"      · {name}")
    if missing:
        errors.append(f"нет перевода для {len(missing)} подписей")
        print("\n  НЕ ПЕРЕВЕДЕНО:")
        for text in sorted(missing):
            print(f"      - {text!r}")

    # --- 2. 模型的 choices 枚举---------------------------
    enums = enum_labels()
    bad_enums = untranslated_enums()
    print(f"\n  Перечислений в choices:       {len(enums) + len(ENUM_SKIP)}")
    print(f"  Из них не переводятся:        {len(ENUM_SKIP)}"
          f" ({', '.join(sorted(ENUM_SKIP))})")
    print(f"  Переведено (portal/labels):   {len(enums) - len(bad_enums)}")
    if bad_enums:
        errors.append(f"нет перевода для {len(bad_enums)} перечислений")
        print("\n  НЕ ПЕРЕВЕДЕНО:")
        for text in sorted(bad_enums):
            print(f"      - {text!r}")

    # --- 3. 字典的值-------------------------------------
    refs = reference_values()
    bad_refs = untranslated_reference_values()
    print(f"\n  Значений справочников:        {len(refs)}")
    print(f"  Переведено (portal/labels):   {len(refs) - len(bad_refs)}")
    if bad_refs:
        errors.append(f"нет перевода для {len(bad_refs)} значений справочников")
        print("\n  НЕ ПЕРЕВЕДЕНО:")
        for text in sorted(bad_refs):
            print(f"      - {text!r}")

    # --- 4. 管理后台的标签---------------------------
    admin = admin_labels()
    bad_admin = untranslated_admin_labels()
    print(f"\n  Подписей админ-панели:        {len(admin)}")
    print(f"  Переведено (portal/labels):   {len(admin) - len(bad_admin)}")
    overrides = admin_overrides()
    print(f"  Исключений из словаря страниц: {len(overrides)}"
          f" ({', '.join(sorted(overrides))})")
    if bad_admin:
        errors.append(f"нет перевода для {len(bad_admin)} подписей админ-панели")
        print("\n  НЕ ПЕРЕВЕДЕНО:")
        for text in sorted(bad_admin):
            print(f"      - {text!r}")

    # --- 5. 自动创建的 M2M 关联模型的标签-------------------
    through = through_labels()
    bad_through = untranslated_through_labels()
    print(f"\n  Подписей связей M2M:          {len(through)}")
    print(f"  Переведено (portal/labels):   {len(through) - len(bad_through)}")
    if bad_through:
        errors.append(f"нет перевода для {len(bad_through)} подписей связей M2M")
        print("\n  НЕ ПЕРЕВЕДЕНО:")
        for text in sorted(bad_through):
            print(f"      - {text!r}")

    # --- 6. 界面外壳文本--------------------------------
    print(f"\n  Текстов оболочки (portal/i18n.UI): {len(UI)}")
    for key, row in UI.items():
        if len(row) != 3:
            errors.append(f"UI[{key!r}]: ожидалось 3 языка, получено {len(row)}")
            continue
        for idx, lang in enumerate(LANGS):
            if not str(row[idx]).strip():
                errors.append(f"UI[{key!r}]: пустой перевод для {lang}")

    # --- 7. 空格：zh 译文中是否残留俄语字母---------
    bad = []
    for key, row in UI.items():
        for idx, lang in enumerate(LANGS):
            if lang == "ru":
                continue
            text = str(row[idx])
            letters = {ch.lower() for ch in text if ch.lower() in CYRILLIC}
            # 只允许 GOST 清单中的缩写
            if letters - {"ф", "г", "и", "с"} and lang == "zh":
                bad.append((key, lang, text))
    if bad:
        print(f"\n  ВНИМАНИЕ: кириллица в китайских текстах ({len(bad)}):")
        for key, lang, text in bad[:10]:
            print(f"      · {key} [{lang}]: {text}")

    # --- 8. 翻译演示-------------------------------------
    print("\n  Примеры перевода:")
    for sample in ("Заказы", "Статус", "Подписание", "Инвойс", "Сертификаты"):
        print(f"      {sample:<18} zh={tr(sample, 'zh'):<16} en={tr(sample, 'en')}")

    print()
    print("=" * 72)
    if errors:
        print("ПРОВЕРКА НЕ ПРОЙДЕНА:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    print("ПРОВЕРКА ПРОЙДЕНА: подписи блоков, перечисления, значения "
          "справочников, подписи админ-панели, подписи связей M2M и тексты "
          "оболочки переведены.")
    print("=" * 72)


if __name__ == "__main__":
    main()
