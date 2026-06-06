import json
import logging
from glob import glob
from pathlib import Path

logger = logging.getLogger(__name__)


def file_pool(input: dict[str, str | list[str]]):
    def get_from_cache(category, name):
        cash_file = Path(f".cache/{name}/_all.json")
        output = json.loads(cash_file.read_text())["output"]
        result = []
        for i in output:
            result.extend(i[category])
        return result

    full_path_input = {}

    for key, value in input.items():
        if isinstance(value, str):
            if Path(f".cache/{value}/_all.json").exists():
                full_path_input[key] = sorted(get_from_cache(key, value))
            else:
                full_path_input[key] = sorted(glob(value))
        elif isinstance(value, list):
            full_path = []
            for i, glob_result in [(j, glob(j)) for j in value]:
                if Path(f".cache/{i}/_all.json").exists():
                    full_path.extend(sorted(get_from_cache(key, i)))
                else:
                    full_path.extend(glob_result)
            full_path_input[key] = [sorted(full_path)]

    result = []
    for key, value in full_path_input.items():
        for index, file in enumerate(value):
            if isinstance(file, str):
                if index < len(result):
                    result[index][key] = [file]
                else:
                    result.append({key: [file]})
            if isinstance(file, list):
                if index < len(result):
                    result[index][key] = file
                else:
                    result.append({key: file})

    agr = {k: len(v) for k, v in full_path_input.items()}
    if min(agr.values()) != max(agr.values()):
        logger.error(f"Кол-во файлов в разных категориях разное: {agr}!!!")
        logger.error(
            f"Будут переданны наборы по наименьшей категории. Всего наборов {min(agr.values())}"
        )

    clean_result = []
    missed_count = 0
    for i in result:
        if len(i.keys()) == len(input.keys()):
            clean_result.append(i)
        else:
            missed_count += 1
    return clean_result


if __name__ == "__main__":
    logging.basicConfig(
        level="DEBUG",
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    result = file_pool(
        {
            "main": "tests/data/file_pool_test/test01/arhive[0-9][0-9].txt",
        }
    )
    assert result == [
        {"main": ["tests/data/file_pool_test/test01/arhive01.txt"]},
        {"main": ["tests/data/file_pool_test/test01/arhive02.txt"]},
        {"main": ["tests/data/file_pool_test/test01/arhive03.txt"]},
    ], f"Неправильный результат {result}"

    result = file_pool(
        {
            "main": "tests/data/file_pool_test/test01/arhive[0-9][0-9].txt",
            "other": "tests/data/file_pool_test/test02/bed[0-9][0-9].txt",
            "third": "tests/data/file_pool_test/test02_two/bed[0-9][0-9].txt",
        }
    )
    assert result == [
        {
            "main": ["tests/data/file_pool_test/test01/arhive01.txt"],
            "other": ["tests/data/file_pool_test/test02/bed01.txt"],
            "third": ["tests/data/file_pool_test/test02_two/bed01.txt"],
        },
        {
            "main": ["tests/data/file_pool_test/test01/arhive02.txt"],
            "other": ["tests/data/file_pool_test/test02/bed02.txt"],
            "third": ["tests/data/file_pool_test/test02_two/bed02.txt"],
        },
        {
            "main": ["tests/data/file_pool_test/test01/arhive03.txt"],
            "other": ["tests/data/file_pool_test/test02/bed03.txt"],
            "third": ["tests/data/file_pool_test/test02_two/bed03.txt"],
        },
    ], f"Неправильный результат {result}"

    result = file_pool(
        {
            "main": "tests/data/file_pool_test/test01/arhive[0-9][0-9].txt",
            "bed": "tests/data/file_pool_test/test02/bed[0-9][0-9].txt",
        }
    )
    assert result == [
        {
            "main": ["tests/data/file_pool_test/test01/arhive01.txt"],
            "bed": ["tests/data/file_pool_test/test02/bed01.txt"],
        },
        {
            "main": ["tests/data/file_pool_test/test01/arhive02.txt"],
            "bed": ["tests/data/file_pool_test/test02/bed02.txt"],
        },
        {
            "main": ["tests/data/file_pool_test/test01/arhive03.txt"],
            "bed": ["tests/data/file_pool_test/test02/bed03.txt"],
        },
    ], f"Неправильный результат {result}"

    result = file_pool(
        {
            "main": [
                "tests/data/raw/*.zip",
                "tests/data/file_pool_test/test01/arhive[0-9][0-9].txt",
            ],
        }
    )
    assert result == [
        {
            "main": [
                "tests/data/file_pool_test/test01/arhive01.txt",
                "tests/data/file_pool_test/test01/arhive02.txt",
                "tests/data/file_pool_test/test01/arhive03.txt",
                "tests/data/raw/test_data.zip",
                "tests/data/raw/test_data_2.zip",
            ],
        }
    ], f"Неправильный результат {result}"

    Path(".cache/test_data/_all.json").write_text(
        json.dumps(
            {
                "input": [
                    {"main": ["tests/data/raw/test_data.zip"]},
                    {"main": ["tests/data/raw/test_data_2.zip"]},
                ],
                "output": [
                    {
                        "main": [
                            "tests/data/unpacked/test_data_2_test_data_res_FinalReport.txt.gz"
                        ]
                    },
                    {
                        "main": [
                            "tests/data/unpacked/test_data_test_data_res_FinalReport.txt.gz"
                        ]
                    },
                ],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    result = file_pool(
        {
            "main": "test_data",
        }
    )
    assert result == [
        {"main": ["tests/data/unpacked/test_data_2_test_data_res_FinalReport.txt.gz"]},
        {"main": ["tests/data/unpacked/test_data_test_data_res_FinalReport.txt.gz"]},
    ], f"Неправильный результат {result}"

    result = file_pool(
        {
            "main": ["test_data"],
        }
    )
    assert result == [
        {
            "main": [
                "tests/data/unpacked/test_data_2_test_data_res_FinalReport.txt.gz",
                "tests/data/unpacked/test_data_test_data_res_FinalReport.txt.gz",
            ]
        },
    ], f"Неправильный результат {result}"
