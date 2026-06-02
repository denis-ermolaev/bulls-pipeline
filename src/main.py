import logging
import shutil
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


@register("prepare_data")
def prepare_data(step: PrepareDataStep):
    # {'type': 'prepare_data', 'enabled': True, 'redo': False, 'input_dir': 'data/raw/', 'output_dir': 'data/unpacked/'}
    cash_file = Path(f".cache/{step.type}")
    if cash_file.exists():
        cash = cash_file.read_text()
    else:
        cash = None

    if not step.enabled and cash == fingerprint(PrepareDataStep):
        return

    if step.redo or cash != fingerprint(PrepareDataStep):
        shutil.rmtree(Path(step.output_dir))

        process_archives(step.input_dir, step.output_dir)

        if not cash_file.exists():
            cash_file.touch()
        cash_file.write_text(fingerprint(PrepareDataStep))


if __name__ == "__main__":
    if not Path(".cache").exists():
        Path(".cache").mkdir()

    logging.basicConfig(
        level="DEBUG",
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    for step in config.pipeline_steps:
        handler = STEP_HANDLERS[step.type]
        handler(step)
