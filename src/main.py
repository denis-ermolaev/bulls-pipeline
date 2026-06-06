import json
import logging
from functools import partial
from multiprocessing import Pool
from pathlib import Path

from tqdm import tqdm

from src.config.config import config
from src.config.schema import PrepareDataStep, StepsFunctionReturn, VCFconverterStep
from src.engine.convert_genetic_maps import convert_genetic_maps
from src.engine.initial_prepare_data import process_archives
from src.engine.vcf_converter import process_file
from src.utils.file_pool import file_pool as make_file_pool
from src.utils.fingerprint import fingerprint

STEP_HANDLERS = {}


def register(name):
    def wrapper(fn):
        STEP_HANDLERS[name] = fn
        return fn

    return wrapper


def fingerprint_handler(func):
    def wrapper(input: dict[str, list[str]], step, **kwargs):
        main_files = [Path(i).stem for i in input["main"]]
        main_files_str = "-".join(main_files)
        input_for_key: str = str(tuple(input.values()))
        cash_file = Path(f".cache/{step.name}/{main_files_str}")
        hash = None
        output = []
        if cash_file.exists():
            try:
                cache = json.loads(cash_file.read_text())
                hash = cache["hash"]
                output = cache[input_for_key]
            except json.decoder.JSONDecodeError:
                pass
            except KeyError:  # Если нужных ключей нету, значит конфига нету
                pass
        else:
            cash_file.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        if not step.enabled and hash == fingerprint(step.name, input, output):
            logging.debug(
                f"[{step.name}-{main_files_str}]. SKIP (fingerprint match OR deactive)"
            )
            return output

        if step.redo or hash != fingerprint(step.name, input, output):
            logging.debug(f"[{step.name}-{main_files_str}]. Запуск обработки")
            # input: dict[str, list[str]], output_dir: str -> dict[str, str | list[str]]
            output = func(input=input, output_dir=step.output_dir, **kwargs)

            hash = fingerprint(step.name, input, output)

            logging.debug(f"[{step.name}-{main_files_str}]. Новый хэш {hash}")
            cash_file.write_text(json.dumps({"hash": hash, input_for_key: output}))
        else:
            logging.debug(f"[{step.name}-{main_files_str}]. SKIP (files already done)")

        return output

    return wrapper


def worker(input, func, step, **kwargs):
    func = fingerprint_handler(func)
    return func(
        input=input,
        step=step,
        **kwargs,
    )


def steps_decorator(func):
    def wrapper(step):
        if not step.output_dir.exists():
            step.output_dir.mkdir(parents=True, exist_ok=True)

        data: StepsFunctionReturn = func(step)
        logging.debug(f"[{step.name}]. Пул файлов для обработки {data.file_pool}")
        output_files_clean = []

        with Pool(step.params.threads) as p:
            for result in tqdm(
                p.imap_unordered(
                    partial(worker, step=step, func=data.func), data.file_pool
                ),
                total=len(data.file_pool),
                desc=data.desc,
            ):
                output_files_clean.append(result)
        Path(f".cache/{step.name}/_all.json").write_text(
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
@register("initial_prepare_data")
@steps_decorator
def prepare_data(step: PrepareDataStep) -> StepsFunctionReturn:
    return StepsFunctionReturn(
        **{
            "file_pool": make_file_pool(step.input.model_dump()),
            "desc": "Подготовка исходных данных",
            "func": process_archives,
        }
    )


## 1.2 Конвертация в VCF ----
@register("convert_recombination_map")
@steps_decorator
def convert_recombination_map(
    step,
) -> StepsFunctionReturn:
    return StepsFunctionReturn(
        **{
            "file_pool": make_file_pool(step.input.model_dump()),
            "desc": "Конвертация карты рекомбинации",
            "func": convert_genetic_maps,
        }
    )


# 2. Конвертация в VCF ----
@register("vcf_converter")
@steps_decorator
def conversion_final_report_to_vcf(
    step: VCFconverterStep,
) -> StepsFunctionReturn:
    return StepsFunctionReturn(
        **{
            "file_pool": make_file_pool(step.input.model_dump()),
            "desc": "Конвертация в VCF",
            "func": process_file,
        }
    )


if __name__ == "__main__":
    logging.basicConfig(
        level="DEBUG",
        format="\n%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("src.engine.initial_prepare_data").disabled = True
    logging.getLogger("src.engine.vcf_converter").disabled = True

    if not Path(".cache").exists():
        Path(".cache").mkdir()
    for step in config.pipeline_steps:
        logging.debug(f"Начало шага {step.name}. Настройки {step}")
        if STEP_HANDLERS.get(step.engine):
            handler = STEP_HANDLERS[step.engine]
            handler(step)
        else:
            logging.error(f"Ф-и обработчика для {step.engine} не существует")
