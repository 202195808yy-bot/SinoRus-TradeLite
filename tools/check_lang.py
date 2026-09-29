# -*- coding: utf-8 -*-
"""Проверка полноты словаря переводов (portal/labels.py, portal/i18n.py).

Проверяются три вещи:

* подписи блоков данных — прогон всех провайдеров portal/datasets.py;
* перечисления из ``choices`` моделей (статусы, виды документов, единицы
  измерения) — они попадают в ячейки значениями, а не подписями;
* тексты оболочки интерфейса (portal/i18n.UI).

Ошибкой считается непереведённая подпись блока, непереведённое
перечисление и пустой перевод в текстах оболочки.

Запуск:  python tools/check_lang.py
"""

import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tradehub.settings")
django.setup()

from portal.i18n import LANGS, UI, tr                      # noqa: E402
from portal.langcheck import (ENUM_SKIP, enum_labels, reference_values,  # noqa: E402
                              scan, untranslated_enums,
                              untranslated_reference_values)

CYRILLIC = set("абвгдеёжзийклмнопрстуфхцчшщъыьэюя")


def main():
    print("=" * 72)
    print("ПОЛНОТА ПЕРЕВОДОВ ИНТЕРФЕЙСА (portal/labels.py, portal/i18n.py)")
    print("=" * 72)

    errors = []

    # --- 1. Подписи блоков данных -------------------------------------
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

    # --- 2. Перечисления из choices моделей ---------------------------
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

    # --- 3. Значения справочников -------------------------------------
    refs = reference_values()
    bad_refs = untranslated_reference_values()
    print(f"\n  Значений справочников:        {len(refs)}")
    print(f"  Переведено (portal/labels):   {len(refs) - len(bad_refs)}")
    if bad_refs:
        errors.append(f"нет перевода для {len(bad_refs)} значений справочников")
        print("\n  НЕ ПЕРЕВЕДЕНО:")
        for text in sorted(bad_refs):
            print(f"      - {text!r}")

    # --- 4. Тексты оболочки интерфейса --------------------------------
    print(f"\n  Текстов оболочки (portal/i18n.UI): {len(UI)}")
    for key, row in UI.items():
        if len(row) != 3:
            errors.append(f"UI[{key!r}]: ожидалось 3 языка, получено {len(row)}")
            continue
        for idx, lang in enumerate(LANGS):
            if not str(row[idx]).strip():
                errors.append(f"UI[{key!r}]: пустой перевод для {lang}")

    # --- 5. Пробелы: остались ли русские буквы в zh-переводах ---------
    bad = []
    for key, row in UI.items():
        for idx, lang in enumerate(LANGS):
            if lang == "ru":
                continue
            text = str(row[idx])
            letters = {ch.lower() for ch in text if ch.lower() in CYRILLIC}
            # допускаются только аббревиатуры ГОСТ-списка
            if letters - {"ф", "г", "и", "с"} and lang == "zh":
                bad.append((key, lang, text))
    if bad:
        print(f"\n  ВНИМАНИЕ: кириллица в китайских текстах ({len(bad)}):")
        for key, lang, text in bad[:10]:
            print(f"      · {key} [{lang}]: {text}")

    # --- 6. Демонстрация перевода -------------------------------------
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
          "справочников и тексты оболочки переведены.")
    print("=" * 72)


if __name__ == "__main__":
    main()
