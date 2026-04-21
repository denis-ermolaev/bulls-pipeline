import glob
import zipfile
import gzip
from dotenv import load_dotenv
import os
import logging


logger = logging.getLogger(__name__)

def process_archives(input_root, output_root):
    """
    Рекурсивно ищет все .zip архивы в input_root, находит в них файлы
    *_FinalReport.txt, сжимает их в отдельные .gz и сохраняет в output_root.

    Параметры:
    input_root (str): Корневая папка для поиска .zip архивов (например, 'data/raw').
    output_root (str): Папка для сохранения результатов (например, 'data/unpacked').

    thintergen_share_geno_VM2_1.zip -> thintergen_share_geno_VM2_1_FinalReport.txt.gz
    """

    logger.info(f"Начинаю обработку архивов в {input_root}")
    # Убедимся, что выходная директория существует
    os.makedirs(output_root, exist_ok=True)

    logger.info(f"Поиск .zip архивов в '{input_root}' и всех подпапках...")

    # Рекурсивный поиск всех .zip файлов
    # `recursive=True` заставляет glob искать и в поддиректориях
    zip_files_path = os.path.join(input_root, "**", "*.zip")
    all_zip_files = glob.glob(zip_files_path, recursive=True)

    if not all_zip_files:
        logger.error("Не найдено ни одного .zip архива.")
        return

    logger.info(f"Найдено {len(all_zip_files)} архивов. Начинаю обработку...\n")

    # --- Шаг 2: Обработка каждого архива ---

    total_reports_found = 0
    total_skipped = 0

    for zip_path in all_zip_files:
        logger.debug(f"🔍 Открываю архив: {os.path.basename(zip_path)}")
        try:
            # Открываем .zip архив в режиме чтения
            with zipfile.ZipFile(zip_path, "r") as archive:
                # Получаем список всех файлов внутри архива
                for internal_file_name in archive.namelist():
                    is_macos_system_file = internal_file_name.startswith(
                        "__MACOSX/"
                    ) or os.path.basename(internal_file_name).startswith("._")

                    if is_macos_system_file:
                        logger.debug(f"-> Пропускаю системный файл: {internal_file_name}")
                        continue  # Переходим к следующему файлу в архиве

                    # Проверяем, соответствует ли файл нашему критерию
                    if internal_file_name.endswith("_FinalReport.txt"):
                        total_reports_found += 1
                        # Формируем имя и путь для нового .gz файла
                        base_name = os.path.basename(internal_file_name)
                        output_gz_path = os.path.join(output_root, base_name + ".gz")
                        if os.path.exists(output_gz_path):
                            logger.debug(
                                f"-> 🟡 Файл уже существует, пропускаю: {output_gz_path}"
                            )
                            total_skipped += 1
                            continue  # Переходим к следующему файлу
                        logger.debug(f"-> Найден файл: {internal_file_name}. Обработка...")
                        # Извлекаем содержимое файла в память (в виде байтов)
                        with archive.open(internal_file_name) as file_in_zip:
                            file_content = file_in_zip.read()
                        # Сжимаем содержимое и записываем в новый файл
                        with gzip.open(output_gz_path, "wb") as f_out:
                            f_out.write(file_content)

                        logger.debug(f"✅ Сжат и сохранен как: {output_gz_path}")

        except zipfile.BadZipFile:
            logger.error(
                f"❌ ОШИБКА: Файл '{os.path.basename(zip_path)}' поврежден или не является zip-архивом."
            )
        except Exception as e:
            logger.error(f"❌ Непредвиденная ОШИБКА при обработке {zip_path}: {e}")

    logger.info(
        f"--- Обработка завершена. Всего найдено и сжато {total_reports_found} файлов FinalReport. Из них пропущено, т.к они уже были готовы {total_skipped} ---"
    )


if __name__ == "__main__":
    load_dotenv()

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )

    input_directory = os.getenv("PATH_TO_RAW")
    output_directory = os.getenv("PATH_TO_PREPARED")

    # TEST MODE
    test_mode = True if os.getenv('TEST_MODE', 'False') == "True" else False
    if test_mode:
        input_directory = os.getenv("PATH_TO_RAW_TEST")
        output_directory = os.getenv("PATH_TO_PREPARED_TEST")

    process_archives(input_directory, output_directory)
