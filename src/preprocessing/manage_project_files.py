import gzip
import logging
import os
import zipfile
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def process_archives(
    input: dict[str, list[str]], output_dir: str
) -> dict[str, str | list[str]]:
    """
    Открывает архив input_zip, находит в нём файл
    *_FinalReport.txt, сжимает их в отдельный .gz и сохраняет в output_file.

    Параметры:
    input (dict): целевой архив (например, 'data/raw/thintergen_share_geno_VM2_1.zip').
    output_dir (str): директория для сохранения (например, 'data/unpacked/').
    Возвращает:
    output_files (list[str]) - ['tests/data/unpacked/test_data_res_FinalReport.txt.gz']
    Заканчиваются на _FinalReport.txt.gz

    thintergen_share_geno_VM2_1.zip -> thintergen_share_geno_VM2_1_FinalReport.txt.gz
    """
    input_file = input["main"][0]  # Берём первый, движок подразумевает 1 файл
    logger.info(f"Начинаю обработку архива {input_file}")

    zip_path = input_file

    logger.debug(f"🔍 Открываю архив: {os.path.basename(zip_path)}")

    output_files = []
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
                    output_gz_path = (
                        Path(output_dir)
                        / f"{Path(input_file).stem}_{internal_file_name}"
                    ).with_suffix(".txt.gz")
                    # if os.path.exists(output_gz_path):
                    #     logger.debug(
                    #         f"-> 🟡 Файл уже существует, пропускаю: {output_gz_path}"
                    #     )
                    #     continue  # Переходим к следующему файлу
                    logger.debug(f"-> Найден файл: {internal_file_name}. Обработка...")
                    # Извлекаем содержимое файла в память (в виде байтов)
                    with archive.open(internal_file_name) as file_in_zip:
                        file_content = file_in_zip.read()

                    output_gz_path.parent.mkdir(
                        parents=True,
                        exist_ok=True,
                    )
                    # Сжимаем содержимое и записываем в новый файл
                    with gzip.open(output_gz_path, "wb") as f_out:
                        f_out.write(file_content)

                    logger.debug(f"✅ Сжат и сохранен как: {output_gz_path}")
                    output_files.append(str(output_gz_path))

    except zipfile.BadZipFile:
        logger.error(
            f"❌ ОШИБКА: Файл '{os.path.basename(zip_path)}' поврежден или не является zip-архивом."
        )
    except Exception as e:
        logger.error(f"❌ Непредвиденная ОШИБКА при обработке {zip_path}: {e}")

    logger.info("--- Обработка завершена. ---")
    return {"main": output_files}


if __name__ == "__main__":
    load_dotenv()

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    print(process_archives("tests/data/raw/test_data.zip", "tests/data/unpacked/"))
