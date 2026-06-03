import glob
import json
import logging
from functools import partial
from multiprocessing import Pool
from pathlib import Path

from tqdm import tqdm

from src.config.config import config
from src.config.schema import (
    ConversionFinalReportToVcfStep,
    PrepareDataStep,
    StepsFunctionReturn,
)
from src.preprocessing.main import process_file
from src.preprocessing.manage_project_files import process_archives
from src.utils.fingerprint import fingerprint

STEP_HANDLERS = {}


def register(name, worker):
    def wrapper(fn):
        STEP_HANDLERS[name] = (fn, worker)
        return fn

    return wrapper


def fingerprint_handler(func):
    def wrapper(file_path, step, **kwargs):
        cash_file = Path(f".cache/{step.type}/{Path(file_path).stem}")
        hash = None
        output_files = []
        if cash_file.exists():
            try:
                cache = json.loads(
                    cash_file.read_text()
                )  # json.decoder.JSONDecodeError:
                hash = cache["hash"]
                output_files = cache[file_path]
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
            PrepareDataStep, [file_path], output_files
        ):
            logging.debug(
                f"[{step.type}-{Path(file_path).stem}]. SKIP (fingerprint match OR deactive)"
            )
            return output_files

        if step.redo or hash != fingerprint(PrepareDataStep, [file_path], output_files):
            logging.debug(f"[{step.type}-{Path(file_path).stem}]. Запуск обработки")

            output_files = func(
                file_path, **kwargs
            )  # process_archives(file_path, step.output_dir)

            hash = fingerprint(PrepareDataStep, [file_path], output_files)

            logging.debug(f"[{step.type}-{Path(file_path).stem}]. Новый хэш {hash}")
            cash_file.write_text(json.dumps({"hash": hash, file_path: output_files}))
        else:
            logging.debug(
                f"[{step.type}-{Path(file_path).stem}]. SKIP (files already done)"
            )

        return output_files

    return wrapper


def steps_decorator(func):
    def wrapper(step, worker):
        if not step.output_dir.exists():
            step.output_dir.mkdir(parents=True, exist_ok=True)

        data: StepsFunctionReturn = func(step)
        logging.debug(f"[{step.type}]. Пул файлов для обработки {data.file_pool}")
        output_files_clean = []

        with Pool(step.threads) as p:
            for result in tqdm(
                p.imap_unordered(
                    partial(
                        worker,
                        step=step,
                    ),
                    data.file_pool,
                ),
                total=len(data.file_pool),
                desc=data.desc,
            ):
                output_files_clean.extend(result)

        Path(f".cache/{step.type}/_all.json").write_text(
            json.dumps(
                {
                    "input": data.file_pool,
                    "output": output_files_clean,
                },
                indent=2,
                ensure_ascii=False,
            )
        )

    return wrapper


# 1. Подготовка данных ----
def _prepare_data(file_path, step):
    process_archives_decorate = fingerprint_handler(process_archives)
    return process_archives_decorate(
        file_path=file_path,
        step=step,
        output_dir=step.output_dir,
    )


@register("prepare_data", _prepare_data)
@steps_decorator
def prepare_data(step: PrepareDataStep) -> StepsFunctionReturn:
    """
    Подготовка данных с помощью многопоточности
    """
    file_pool = sorted(list(glob.glob(step.input_glob)))
    # (file_pool, desc)

    return StepsFunctionReturn(
        **{
            "file_pool": file_pool,
            "desc": "Подготовка исходных данных",
        }
    )


# 2. Конвертация в VCF ----
def _conversion_final_report_to_vcf(
    file_path,
    step: ConversionFinalReportToVcfStep,
):
    process_file_decorate = fingerprint_handler(process_file)
    return process_file_decorate(
        file_path=file_path,
        step=step,
        path_to_result=step.output_dir,
    )


@register("conversion_final_report_to_vcf", _conversion_final_report_to_vcf)
@steps_decorator
def conversion_final_report_to_vcf(
    step: ConversionFinalReportToVcfStep,
) -> StepsFunctionReturn:
    """
    Подготовка данных с помощью многопоточности
    """

    file_pool = sorted(step.input)
    return StepsFunctionReturn(
        **{
            "file_pool": file_pool,
            "desc": "Конвертация в VCF",
        }
    )


if __name__ == "__main__":
    if not Path(".cache").exists():
        Path(".cache").mkdir()

    logging.basicConfig(
        level="DEBUG",
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("src.preprocessing.main").disabled = True
    logging.getLogger("src.preprocessing.manage_project_files").disabled = True

    for step in config.pipeline_steps:
        logging.debug(f"Начало шага {step.type}. Настройки {step}")
        if STEP_HANDLERS.get(step.type):
            # handler - многопоточная ф-я обработчик, использующая handler_worker
            # handler_worker - однопоточная ф-я обработчик
            handler, handler_worker = STEP_HANDLERS[step.type]
            handler(step, handler_worker)
        else:
            logging.error(f"Ф-и обработчика для {step.type} не существует")
