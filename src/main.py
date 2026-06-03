import glob
import json
import logging
from functools import partial
from multiprocessing import Pool
from pathlib import Path

from src.config.config import config
from src.config.schema import PrepareDataStep
from src.preprocessing.manage_project_files import process_archives
from src.utils.fingerprint import fingerprint

STEP_HANDLERS = {}


def register(name):
    def wrapper(fn):
        STEP_HANDLERS[name] = fn
        return fn

    return wrapper


# 1. Подготовка данных ----
def _prepare_data(input_zip, step: PrepareDataStep):
    """
    Обработка одного архива
    """
    cash_file = Path(f".cache/{step.type}/{Path(input_zip).stem}")
    hash = None
    output_files = []
    if cash_file.exists():
        try:
            cache = json.loads(cash_file.read_text())  # json.decoder.JSONDecodeError:
            hash = cache["hash"]
            output_files = cache[input_zip]
        except json.decoder.JSONDecodeError:
            pass
        except KeyError:  # Если нужных ключей нету, значит конфига нету
            pass
    else:
        cash_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    if not step.enabled and hash == fingerprint(
        PrepareDataStep, [input_zip], output_files
    ):
        logging.debug(
            f"[{step.type}-{Path(input_zip).stem}]. SKIP (fingerprint match OR deactive)"
        )
        return output_files

    if step.redo or hash != fingerprint(PrepareDataStep, [input_zip], output_files):
        logging.debug(f"[{step.type}-{Path(input_zip).stem}]. Запуск обработки")

        output_files = process_archives(input_zip, step.output_dir)

        hash = fingerprint(PrepareDataStep, [input_zip], output_files)

        logging.debug(f"[{step.type}-{Path(input_zip).stem}]. Новый хэш {hash}")
        cash_file.write_text(json.dumps({"hash": hash, input_zip: output_files}))
    else:
        logging.debug(
            f"[{step.type}-{Path(input_zip).stem}]. SKIP (files already done)"
        )

    return output_files


@register("prepare_data")
def prepare_data(step: PrepareDataStep):
    """
    Подготовка данных с помощью многопоточности
    """
    if not step.output_dir.exists():
        step.output_dir.mkdir(parents=True, exist_ok=True)

    file_pool = sorted(list(glob.glob(step.input_glob)))
    logging.debug(f"[{step.type}]. Пул файлов для обработки {file_pool}")

    with Pool(step.threads) as p:
        output_files = p.map(partial(_prepare_data, step=step), file_pool)

    output_files_clean = []
    for files in output_files:
        output_files_clean.extend(files)
    for file in glob.glob(f"{step.output_dir}/*"):
        if file not in output_files_clean:
            logging.warning(
                f"[{step.type}]. Файл, не входит в результаты обработки: {file}"
            )

    Path(f".cache/{step.type}/_all.json").write_text(
        json.dumps(
            {
                "input": file_pool,
                "output": output_files_clean,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    if not Path(".cache").exists():
        Path(".cache").mkdir()

    logging.basicConfig(
        level="DEBUG",
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    for step in config.pipeline_steps:
        logging.debug(f"Начало шага {step.type}. Настройки {step}")
        if STEP_HANDLERS.get(step.type):
            handler = STEP_HANDLERS[step.type]
            handler(step)
        else:
            logging.error(f"Ф-и обработчика для {step.type} не существует")
