import hashlib
from pathlib import Path

from src.config.config import config
from src.config.schema import PrepareDataStep


def fingerprint(schema, input=False, output=False):
    """
    Хэш:
    input_dir
    +
    config для отдельного шага
    """
    h = hashlib.sha256()

    for step in config.pipeline_steps:
        if isinstance(step, schema):
            result = step

    if input:
        input = sorted(input)
        for file in input:
            file = Path(file)
            if file.is_file():
                stat = file.stat()

                h.update(str(file.relative_to(file)).encode())
                h.update(str(stat.st_size).encode())
                h.update(str(stat.st_mtime_ns).encode())
    if output:
        output = sorted(output)
        for file in output:
            file = Path(file)
            if file.is_file():
                stat = file.stat()

                h.update(str(file.relative_to(file)).encode())
                h.update(str(stat.st_size).encode())
                h.update(str(stat.st_mtime_ns).encode())

    h.update(result.model_dump_json(exclude={"redo"}).encode())

    return h.hexdigest()


if __name__ == "__main__":
    print(
        fingerprint(
            PrepareDataStep,
            ["tests/data/raw/test_data_2.zip"],
            ["tests/data/unpacked/test_data_res_FinalReport.txt.gz"],
        )
    )
