#!/usr/bin/env python3
"""
download_selective.py
Скачивает только указанные папки/файлы из Hugging Face датасета.
Если элемент не существует или не указан – пропускает.
"""

from pathlib import Path

from huggingface_hub import hf_hub_download, snapshot_download

REPO_ID = "denis-ermolaev/bulls-data"
REPO_TYPE = "dataset"
LOCAL_DIR = "."  # корень, куда сохранять (можно "./test_data")
TOKEN = None  # для приватных репозиториев указать токен
RESUME = True

# Перечисли нужные папки или файлы (пути относительно корня репозитория).
# Для папок используй "/**" в конце (рекурсивно). Файлы – как есть.
# Примеры:
SELECTED_PATHS = [
    "bin/**",  # вся папка bin
    "data/genetic_maps/**",  # рекурсивно папку genetic_maps
    "data/manifest/BovineHD_B1.csv",
    "data/reference/ncbi_dataset/data/GCF_002263795.3/GCF_002263795.3_ARS-UCD2.0_genomic.fna",
    "data/reference/ncbi_dataset/data/GCF_002263795.3/GCF_002263795.3_ARS-UCD2.0_genomic.fna.fai",
    "data/ref_panel_test/**",
    "data/bulls-pipeline.tar",
]
# Если нужно загрузить всю папку data рекурсивно: "data/**"


def download_selected(paths: list[str]):
    print(f"Загрузка выбранных файлов/папок из {REPO_ID} в '{LOCAL_DIR}'...")
    # Превращаем относительные пути в абсолютные/нормализованные
    selected_allow = []
    selected_files = []

    for p in paths:
        p = p.strip()
        if not p:
            continue
        # Если путь заканчивается на '**', это рекурсивная папка – подходит для allow_patterns
        if p.endswith("/**"):
            selected_allow.append(p)
        elif "*" in p:  # другие glob-паттерны
            selected_allow.append(p)
        else:
            # Проверим: если это похоже на файл (есть расширение) – будем качать как файл,
            # иначе как папку (добавим /**). Определим эвристикой: есть точка в последней части
            # или путь существует локально (но локально может не быть, смотрим на имя)
            # Проще: добавим в allow_patterns "p/**" для папок и "p" для файлов.
            # Но snapshot_download с allow_patterns понимает glob, можно указывать и файлы.
            # Однако если указать "data/genetic_maps", он не рекурсивно, а только сам файл, если это файл.
            # Лучше явно разделить: если путь имеет расширение (содержит точку в последнем элементе),
            # считаем файлом и используем hf_hub_download. Иначе – папка, добавляем "/**".
            # Более надёжный способ: пробовать скачать как файл через list_repo_files,
            # но для простоты сделаем эвристику.
            if _looks_like_file(p):
                selected_files.append(p)
            else:
                selected_allow.append(f"{p}/**")
                # также попробуем скачать как файл на всякий случай?
                # Если это действительно файл без расширения – тогда нужно уточнить.
                # Для универсальности можно сначала попробовать hf_hub_download для файла,
                # если ошибка – пропустить, но тогда потеряем папку.
                # Лучше полагаться на расширение. Пользователь может указать "myfolder/**" явно.
                # Поэтому оставим так, в SELECTED_PATHS нужно добавлять "/**" для папок.
                pass

    # 1. Скачиваем папки (или glob-шаблоны) через snapshot_download
    if selected_allow:
        print(f"Папки/шаблоны: {selected_allow}")
        snapshot_download(
            repo_id=REPO_ID,
            repo_type=REPO_TYPE,
            local_dir=LOCAL_DIR,
            allow_patterns=selected_allow,
            ignore_patterns=None,  # можно добавить исключения, если нужно
            resume_download=RESUME,
            token=TOKEN,
        )
    else:
        print("Папки не выбраны, пропускаем snapshot_download.")

    # 2. Скачиваем отдельные файлы (для них allow_patterns в snapshot иногда неудобен)
    for f in selected_files:
        print(f"Скачивание файла: {f}")
        try:
            hf_hub_download(
                repo_id=REPO_ID,
                repo_type=REPO_TYPE,
                filename=f,
                local_dir=LOCAL_DIR,
                token=TOKEN,
            )
            print(f"  ✓ {f}")
        except Exception as e:
            print(f"  ✗ Ошибка при скачивании {f}: {e}")

    print("✅ Выборочная загрузка завершена.")


def _looks_like_file(path: str) -> bool:
    """Эвристика: считаем файлом, если последний сегмент содержит точку."""
    # Исключаем очевидные папки (например, "bin", "data/genetic_maps")
    last = Path(path).name
    return "." in last and not last.endswith("/")


if __name__ == "__main__":
    download_selected(SELECTED_PATHS)
