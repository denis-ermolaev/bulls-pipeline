# Установка зависемостей
install:
	uv sync

# Запуск preprocessing
run:
	uv run python src/preprocessing/main.py

# Отдельный запуск модулей
prepare_files:
	uv run python src/preprocessing/manage_project_files.py

# Вспомогательные команды
requirements:
	uv export --format requirements-txt > requirements.txt

## Запустить проверку ошибок/типов и т.п mypy
mypy:
	uv run mypy . --cache-dir /dev/null