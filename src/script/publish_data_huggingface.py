#!/usr/bin/env python3
"""
upload_to_huggingface.py
Загружает папки и/или отдельные файлы на Hugging Face Hub.

hf auth login - для API key
"""

import os

from huggingface_hub import HfApi

# ========== НАСТРОЙКИ ==========
REPO_ID = "denis-ermolaev/bulls-data"
LOCAL_PATHS = [
    "bin",
    "data/genetic_maps",
    "data/genetic_maps_holstein",
    "data/manifest",
    "data/old_reference",
    "data/ref_panel",
    "data/reference",
    "data/usa_bulls",
    "data/Animal_QTLdb_release59_cattleARS_UCD2.bed.gz",
    "data/Bos_taurus.ARS-UCD2.0.115.gtf.gz",
    "data/goa_cow.gaf.gz",
    "data/Nellore_cattle_gwas_product.txt",
    "data/qtldat545053924.csv",
    "data/bulls-pipeline.tar",
]
REPO_TYPE = "dataset"
IGNORE_PATTERNS = ["*.tmp", "*.log", "__pycache__", "*.pyc"]
RENAME_MAP = {
    "data_public": "data",
}
# ===============================


def upload_items():
    api = HfApi()

    # Создаём репозиторий, если нужно
    try:
        api.create_repo(repo_id=REPO_ID, repo_type=REPO_TYPE, exist_ok=True)
        print(f"✓ Репозиторий {REPO_ID} готов")
    except Exception as e:
        print(f"✗ Ошибка создания репозитория: {e}")
        return

    for local_path in LOCAL_PATHS:
        # Проверяем существование
        if not os.path.exists(local_path):
            print(f"⚠ Пропуск (не найден): {local_path}")
            continue

        # Определяем целевое имя (с учётом RENAME_MAP)
        # Для файлов — сохраняем родительскую структуру, если она задана в RENAME_MAP
        original_name = os.path.normpath(local_path)
        target_name = RENAME_MAP.get(original_name, original_name)

        try:
            if os.path.isdir(local_path):
                # Загружаем папку
                print(f"→ Загрузка папки {local_path} -> {target_name}/")
                api.upload_folder(
                    folder_path=local_path,
                    path_in_repo=target_name,
                    repo_id=REPO_ID,
                    repo_type=REPO_TYPE,
                    ignore_patterns=IGNORE_PATTERNS,
                )
            elif os.path.isfile(local_path):
                # Загружаем файл: сохраняем его путь в репо (например, data/file.txt)
                # Если нужно просто в корень или подпапку — настраиваем path_in_repo
                print(f"→ Загрузка файла {local_path} -> {target_name}")
                api.upload_file(
                    path_or_fileobj=local_path,
                    path_in_repo=target_name,
                    repo_id=REPO_ID,
                    repo_type=REPO_TYPE,
                )
            else:
                print(f"⚠ Пропуск (особый объект): {local_path}")
        except Exception as e:
            print(f"  ✗ Ошибка при загрузке {local_path}: {e}")

    print("\n✅ Загрузка завершена!")


if __name__ == "__main__":
    upload_items()
