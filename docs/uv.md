```
# Установить всё
uv sync

# Установили production‑зависимости
uv add pandas pysam
# Установили dev‑зависимости
uv add --dev mypy

# Активировали окружение (по желанию, только для запуска)
source .venv/bin/activate

# Запускаете пайплайн, как раньше
python bulls_pipeline.py --help

# В другом терминале без активации можете использовать uv run
uv run python bulls_pipeline.py --help
```