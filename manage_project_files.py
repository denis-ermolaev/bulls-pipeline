import os
import glob
import zipfile
import gzip


def process_archives(input_root, output_root):
    """
    Рекурсивно ищет все .zip архивы в input_root, находит в них файлы
    *_FinalReport.txt, сжимает их в .gz и сохраняет в output_root.

    Аргументы:
    input_root (str): Корневая папка для поиска .zip архивов (например, 'data/raw').
    output_root (str): Папка для сохранения результатов (например, 'data/unpacked').
    """

    # --- Шаг 1: Подготовка ---

    # Убедимся, что выходная директория существует
    os.makedirs(output_root, exist_ok=True)

    print(f"Поиск .zip архивов в '{input_root}' и всех подпапках...")

    # Рекурсивный поиск всех .zip файлов
    # `recursive=True` заставляет glob искать и в поддиректориях
    zip_files_path = os.path.join(input_root, "**", "*.zip")
    all_zip_files = glob.glob(zip_files_path, recursive=True)

    if not all_zip_files:
        print("Не найдено ни одного .zip архива.")
        return

    print(f"Найдено {len(all_zip_files)} архивов. Начинаю обработку...\n")

    # --- Шаг 2: Обработка каждого архива ---

    total_reports_found = 0

    for zip_path in all_zip_files:
        print(f"🔍 Открываю архив: {os.path.basename(zip_path)}")
        try:
            # Открываем .zip архив в режиме чтения
            with zipfile.ZipFile(zip_path, "r") as archive:
                # Получаем список всех файлов внутри архива
                for internal_file_name in archive.namelist():
                    is_macos_system_file = internal_file_name.startswith(
                        "__MACOSX/"
                    ) or os.path.basename(internal_file_name).startswith("._")

                    if is_macos_system_file:
                        print(f"  -> Пропускаю системный файл: {internal_file_name}")
                        continue  # Переходим к следующему файлу в архиве

                    # Проверяем, соответствует ли файл нашему критерию
                    if internal_file_name.endswith("_FinalReport.txt"):
                        total_reports_found += 1
                        # Формируем имя и путь для нового .gz файла
                        base_name = os.path.basename(internal_file_name)
                        output_gz_path = os.path.join(output_root, base_name + ".gz")
                        if os.path.exists(output_gz_path):
                            print(
                                f"  -> 🟡 Файл уже существует, пропускаю: {output_gz_path}"
                            )
                            total_skipped += 1
                            continue  # Переходим к следующему файлу
                        print(f"  -> Найден файл: {internal_file_name}")
                        # Извлекаем содержимое файла в память (в виде байтов)
                        with archive.open(internal_file_name) as file_in_zip:
                            file_content = file_in_zip.read()
                        # Сжимаем содержимое и записываем в новый файл
                        with gzip.open(output_gz_path, "wb") as f_out:
                            f_out.write(file_content)

                        print(f"  ✅ Сжат и сохранен как: {output_gz_path}")

        except zipfile.BadZipFile:
            print(
                f"  ❌ ОШИБКА: Файл '{os.path.basename(zip_path)}' поврежден или не является zip-архивом."
            )
        except Exception as e:
            print(f"  ❌ Непредвиденная ОШИБКА при обработке {zip_path}: {e}")

    print(
        f"\n--- Обработка завершена. Всего найдено и сжато {total_reports_found} файлов FinalReport. ---"
    )


# --- Как использовать ---
input_directory = "data/raw"
output_directory = "data/unpacked"

process_archives(input_directory, output_directory)
