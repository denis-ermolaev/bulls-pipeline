# Переменные проекта
IMAGE_NAME = bulls-pipeline
CONTAINER_NAME = bulls-pipeline

# Автоматическая проверка: если мы на сервере (есть папка /scratch), добавляем флаг групп.
# Если запускаем дома — флаг будет пустым.
FLAGS = $(shell if [ -d /scratch/storageA ]; then echo "--group-add keep-groups"; fi)

.PHONY: build run stop enter logs stats clean help

#####################################################################################
#
# SECTION: Управление контейнером
#
#####################################################################################

# Справка
all: help

build:
# Поднимаем лимит до 65535 открытых файлов
	podman build --ulimit nofile=65535:65535 -t $(IMAGE_NAME) .

run: stop
	podman run -d \
		--name $(CONTAINER_NAME) \
		$(FLAGS) \
		-v .:/app \
		-it \
		$(IMAGE_NAME)

run_jupyter:
	podman run --rm -it \
		-p 8888:8888 \
		$(FLAGS) \
		-v .:/app \
		$(IMAGE_NAME) \
		jupyter notebook --ip=0.0.0.0 --allow-root --no-browser

stop:
	stop:
	podman rm -f $(CONTAINER_NAME) 2>/dev/null || true

enter:
	podman exec -it $(CONTAINER_NAME) /bin/bash

logs:
	podman logs -f $(CONTAINER_NAME)

stats:
	podman stats $(CONTAINER_NAME)

clean:
	podman image prune -f

help:
	@echo "Доступные команды для управления проектом:"
	@echo "  make build  - Собрать образ"
	@echo "  make run    - Запустить контейнер в фоне (автоопределение сервера)"
	@echo "  make stop   - Остановить и удалить контейнер"
	@echo "  make enter  - Войти в терминал контейнера"
	@echo "  make logs   - Посмотреть логи"
	@echo "  make stats  - Посмотреть загрузку памяти и CPU"
	@echo "  make clean  - Очистить кэш старых образов"


#####################################################################################
#
# SECTION: КОМАНДЫ ВНУТРИ КОНТЕЙНЕРА
#
#####################################################################################

install:
	podman exec $(CONTAINER_NAME) uv sync --no-install-project


run_pipeline: install
	podman exec $(CONTAINER_NAME) python src/preprocessing/main.py


prepare_files: install
	podman exec $(CONTAINER_NAME) python src/preprocessing/manage_project_files.py


tools_bash: install
	podman exec $(CONTAINER_NAME) python src/preprocessing/tools_bash.py


tools_ensembl: install
	podman exec $(CONTAINER_NAME) python src/preprocessing/tools_ensembl.py


#####################################################################################
#
# SECTION: DEV НА ХОСТЕ
#
#####################################################################################


install_host:
	uv sync

requirements_host:
	uv export --format requirements-txt > requirements.txt

# Ручной запуск линтеров и форматирования (флаг -t нужен для красивых цветов в консоли)
pre-commit_host:
	uv run pre-commit run --all-files

# Установка хуков (внутри контейнера обновит папку .git/hooks)
pre-commit-install_host:
	uv run pre-commit install
