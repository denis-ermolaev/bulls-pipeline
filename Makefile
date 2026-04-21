# Установка зависемостей
install:
	pip install -r requirements.txt

# Запуск preprocessing
run_pre:
	python src/preprocessing/main.py



# Отдельный запуск модулей
prepare_files:
	python src/preprocessing/manage_project_files.py

# Вспомогательные команды
requirements:
	pip freeze > requirements.txt