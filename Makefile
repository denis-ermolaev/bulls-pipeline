IMAGE_NAME = bulls-pipeline
CONTAINER_NAME = bulls-pipeline

# Автоматическая проверка: если мы на сервере (есть папка /scratch), добавляем флаг групп.
# Если запускаем дома — флаг будет пустым.
FLAGS = $(shell if [ -d /scratch/storageA ]; then echo "--group-add keep-groups"; fi)

# .PHONY: build run stop enter logs stats clean help install run_pipeline prepare_files tools_bash tools_ensembl

project_preparation:
	@export PATH="$$HOME/.local/bin:$$PATH" && bash tests/preparation_data/project_preparation.sh


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
#                            УПРАВЛЕНИЕ КОНТЕЙНЕРОМ                            #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

build:
	podman build -t $(IMAGE_NAME) .

run: stop
	podman run -d \
		--name $(CONTAINER_NAME) \
		$(FLAGS) \
		-v .:/app \
		-it \
		$(IMAGE_NAME)

run_jupyter:
	podman run --rm -it \
		-p 127.0.0.1:8888:8888 \
		$(FLAGS) \
		-v .:/app \
		$(IMAGE_NAME) \
		jupyter server \
			--ip=0.0.0.0 \
			--port=8888 \
			--no-browser \
			--allow-root \
			--ServerApp.token='' \
			--ServerApp.password=''

stop:
	podman rm -f $(CONTAINER_NAME) 2>/dev/null || true

enter:
	podman exec -it $(CONTAINER_NAME) /bin/bash

logs:
	podman logs -f $(CONTAINER_NAME)

status:
	podman ps --filter "name=$(CONTAINER_NAME)"

# Ресурсы, которые использует контейнер
stats:
	podman stats $(CONTAINER_NAME)

clean:
	podman image prune -f

# ---------------------------------------------------------------------------- #


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
#                           КОМАНДЫ ВНУТРИ КОНТЕЙНЕРА                          #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
install:
	podman exec $(CONTAINER_NAME) uv sync --no-install-project


run_pipeline: install
	podman exec $(CONTAINER_NAME) python src/preprocessing/main.py


run_prepare_files: install
	podman exec $(CONTAINER_NAME) python src/preprocessing/manage_project_files.py


run_tools_bash: install
	podman exec $(CONTAINER_NAME) python src/preprocessing/tools_bash.py


run_tools_ensembl: install
	podman exec $(CONTAINER_NAME) python src/preprocessing/tools_ensembl.py

# ---------------------------------------------------------------------------- #


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
#                                      DEV                                     #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

install_host:
	uv sync

# Ручной запуск линтеров и форматирования (флаг -t нужен для красивых цветов в консоли)
pre-commit_host:
	uv run pre-commit run --all-files

# Установка хуков (внутри контейнера обновит папку .git/hooks)
pre-commit-install_host:
	uv run pre-commit install

# Запуск тестов
test: build
	podman run --rm \
		$(FLAGS) \
		-v .:/app \
		-w /app \
		$(IMAGE_NAME) \
		pytest

requirements_host:
	uv export --format requirements-txt > requirements.txt

# ---------------------------------------------------------------------------- #
