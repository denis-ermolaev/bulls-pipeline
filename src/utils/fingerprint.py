import hashlib
from pathlib import Path
from typing import Literal

from src.config.config import config


def fingerprint(
    name: str,
    input: dict[str, str] | Literal[False] = False,
    output: dict[str, list[str]] | Literal[False] = False,
) -> str:
    """
    Хэш:
    input + config для отдельного шага + output
    """
    h = hashlib.sha256()

    for step in config.pipeline_steps:
        if step.name == name:
            h.update(step.model_dump_json().encode())
            break

    if input:
        input_lst = []
        for i in input.values():
            input_lst.extend(i)
        for file in sorted(input_lst):
            file = Path(file)
            if file.is_file():
                stat = file.stat()

                h.update(str(file).encode())
                h.update(str(stat.st_size).encode())
                h.update(str(stat.st_mtime_ns).encode())
    if output:
        output_lst = []
        for i in output.values():
            output_lst.extend(i)
        for file in sorted(output_lst):
            file = Path(file)
            if file.is_file():
                stat = file.stat()

                h.update(str(file).encode())
                h.update(str(stat.st_size).encode())
                h.update(str(stat.st_mtime_ns).encode())

    return h.hexdigest()


if __name__ == "__main__":
    print(
        fingerprint(
            "prepare_data",
            {
                "main": [
                    "tests/data/raw/test_data_2.zip",
                    "tests/data/raw/test_data_3.zip",
                ],
                "other": ["tests/data/raw/test_data_2.dop"],
            },
            {
                "main": [
                    "tests/data/raw/test_data_2.main",
                    "tests/data/raw/test_data_3.main",
                ],
                "bed": ["tests/data/raw/test_data_2.bed"],
                "fai": ["tests/data/raw/test_data_2.fai"],
            },
        )
    )
