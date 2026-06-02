import hashlib

from src.config.config import config
from src.config.schema import PrepareDataStep


def fingerprint(schema):
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

    if result.input_dir:
        for file in sorted(result.input_dir.rglob("*")):
            if file.is_file():
                stat = file.stat()

                h.update(str(file.relative_to(result.input_dir)).encode())
                h.update(str(stat.st_size).encode())
                h.update(str(stat.st_mtime_ns).encode())
    if result.output_dir:
        for file in sorted(result.output_dir.rglob("*")):
            if file.is_file():
                stat = file.stat()

                h.update(str(file.relative_to(result.output_dir)).encode())
                h.update(str(stat.st_size).encode())
                h.update(str(stat.st_mtime_ns).encode())

    h.update(result.model_dump_json(exclude={"redo"}).encode())

    return h.hexdigest()


if __name__ == "__main__":
    print(fingerprint(PrepareDataStep))
