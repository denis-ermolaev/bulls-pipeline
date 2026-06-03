#!/usr/bin/env python3
"""
download_from_huggingface.py
Скачивает репозиторий (датасет/модель) с Hugging Face Hub в локальную папку.
Если файл уже скачан и не изменился – пропускает.
"""

from huggingface_hub import snapshot_download

REPO_ID = "denis-ermolaev/bulls-data"  # ваш репозиторий
REPO_TYPE = "dataset"  # "dataset", "model" или "space"
LOCAL_DIR = "."  # куда сохранять

# --- Дополнительные опции ---
# Игнорировать определённые файлы (по паттернам, как в .gitignore)
# Пример: исключить .gitattributes, все README и все .md, кроме важного
IGNORE_PATTERNS = [
    "*.tmp",
    "*.log",
    "__pycache__",
    "*.pyc",
    ".gitattributes",
    "README*",
]
# Возобновлять докачку, если файл недокачан (по умолчанию True)
RESUME = True
# Токен не обязателен для публичных репозиториев
TOKEN = None  # или "hf_..." если репозиторий приватный


def download_repo():
    print(f"Скачивание {REPO_ID} (тип: {REPO_TYPE}) в '{LOCAL_DIR}'...")

    # snapshot_download автоматически пропускает файлы,
    # которые уже скачаны и совпадают с хабом.
    # Если файл есть, но изменился – перезаписывает.
    snapshot_download(
        repo_id=REPO_ID,
        repo_type=REPO_TYPE,
        local_dir=LOCAL_DIR,  # сохранять прямо в эту папку
        ignore_patterns=IGNORE_PATTERNS,
        resume_download=RESUME,
        token=TOKEN,  # None -> анонимный доступ
    )
    print("✅ Загрузка завершена.")


if __name__ == "__main__":
    download_repo()
