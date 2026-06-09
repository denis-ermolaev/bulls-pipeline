IMAGE_NAME = bulls-pipeline
CONTAINER_NAME = bulls-pipeline


# Автоматическая проверка: если мы на сервере (есть папка /scratch), добавляем флаг групп.
FLAGS = $(shell if [ -d /scratch/storageA ]; then echo "--group-add keep-groups"; fi)

.PHONY: run_container_with_ssh run_container run_jupyter stop enter run_pipeline


### Подготовка окружения
## Подготовить тестовое окружение
test_project_preparation:
	@export PATH="$$HOME/.local/bin:$$PATH" && bash src/script/project_preparation.sh src/script/test_download_data_huggingface.py

## Подготовить окружение
project_preparation:
	@export PATH="$$HOME/.local/bin:$$PATH" && bash src/script/project_preparation.sh src/script/download_data_huggingface.py


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
#                            УПРАВЛЕНИЕ КОНТЕЙНЕРОМ                            #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

### Управление контейниризацией
## Собрать образ
build:
	podman build -t $(IMAGE_NAME) .


## Запустить контейнер для запуска скриптов пайплайна
run_container: stop
	podman run -d \
		--name $(CONTAINER_NAME) \
		$(FLAGS) \
		-v .:/app \
		-it \
		$(IMAGE_NAME)

## Запустить контейнер с ssh для разработки внутри контейнера
# Подтягивает ssh ключи для авторизации, информацию от git с хоста
run_container_with_ssh: stop
	@PORT=$$((20000 + $$(id -u))); \
	echo "Using port $$PORT"; \
	podman run -d \
		--name $(CONTAINER_NAME) \
		$(FLAGS) \
		-p 127.0.0.1:$$PORT:22 \
		-v ~/.ssh/authorized_keys:/root/.ssh/authorized_keys:ro \
		-v ~/.gitconfig:/root/.gitconfig:ro \
		-v ~/.git-credentials:/home/developer/.git-credentials:ro \
		-v dev-root:/root \
		-v .:/app \
		-v venv_volume:/app/.venv \
		--restart=unless-stopped \
		-it \
		$(IMAGE_NAME)

## Отчистить постоянные тома для dev-контейнера с ssh
clean_persistent_volumes_container_with_ssh:
	podman volume rm dev-root
	podman volume rm venv_volume

## Запустить Jupyter сервер внутри контейнера
run_jupyter:
	podman run --rm -it \
		-p 127.0.0.1::8888
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

## Остановить контейнер
stop:
	podman rm -f $(CONTAINER_NAME) 2>/dev/null || true

## Открыть shell в работающем контейнере
enter:
	podman exec -it $(CONTAINER_NAME) /bin/bash

## Показать логи контейнера
logs:
	podman logs -f $(CONTAINER_NAME)

## Проверить, работает ли контейнер
status:
	podman ps --filter "name=$(CONTAINER_NAME)"

## Потребление ресурсов контейнером
stats:
	podman stats --no-stream $(CONTAINER_NAME)

## Удалить неиспользуемые образы
clean:
	podman image prune -f

# ---------------------------------------------------------------------------- #


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
#                           КОМАНДЫ ВНУТРИ КОНТЕЙНЕРА                          #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
### Команды внутри контейнера
## Синхронизировать зависимости (uv) в контейнере
install:
	podman exec $(CONTAINER_NAME) uv sync --no-install-project


## Запустить пайплайн
run_pipeline:
	podman exec $(CONTAINER_NAME) uv run -m src.main

# ---------------------------------------------------------------------------- #


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
#                                   DEV HOST                                   #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
### Разработка(HOST)
## Установить/обновить зависимости на хосте
install_host:
	uv sync

## Запустить pre-commit
pre-commit_host:
	uv run pre-commit run --all-files

## Установить pre-commit хуки
pre-commit-install_host:
	uv run pre-commit install

## Запуск тестов
test_host: build
	podman run --rm \
		$(FLAGS) \
		-v .:/app \
		-w /app \
		$(IMAGE_NAME) \
		pytest

## Экспортировать список зависимостей
requirements_host:
	uv export --format requirements-txt > requirements.txt

# ---------------------------------------------------------------------------- #


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
#                Работа с публичным репозиторием больших файлов                #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
### Публикация
# Подготовка и загрузка ПУБЛИЧНЫХ файлов на hugging face


## Сохранить образ в архив
publish_save_container_host:
	rm -f data/bulls-pipeline.tar
	podman save -o data/$(IMAGE_NAME).tar $(IMAGE_NAME):latest

# ---------------------------------------------------------------------------- #
