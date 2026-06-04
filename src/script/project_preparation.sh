#!/bin/bash
set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <python_script> [args...]"
    exit 1
fi

echo "==> Checking uv..."
if ! command -v uv &> /dev/null; then
    echo "uv not found. Installing..."
    curl -Ls https://astral.sh/uv/install.sh | bash
    export PATH="$HOME/.local/bin:$PATH"
else
    echo "uv already installed ✔"
fi

echo "==> Ensuring Python is available (via uv)..."
# uv python install подхватит подходящую версию из .python-version или pyproject.toml,
# либо установит последнюю стабильную (если нет никаких указаний)
if ! uv python find &> /dev/null; then
    echo "No Python found. Installing Python via uv..."
    uv python install
    echo "Python installed ✔"
else
    echo "Python already present ✔"
fi

echo "==> Installing project dependencies..."
# Создаст/обновит виртуальное окружение и установит все пакеты из pyproject.toml
uv sync
echo "Dependencies synced ✔"

echo "==> Installing pre-commit hooks..."
if uv run pre-commit install; then
    echo "pre-commit hooks installed ✔"
else
    echo "⚠ Warning: pre-commit install failed. Check if pre-commit is in pyproject.toml."
fi

echo "==> Running data download script..."
DOWNLOAD_SCRIPT="$1"
shift   # убираем первый аргумент, оставляем только параметры

if [ -f "$DOWNLOAD_SCRIPT" ]; then
    uv run python "$DOWNLOAD_SCRIPT" "$@"
else
    echo "❌ $DOWNLOAD_SCRIPT not found!"
    exit 1
fi

echo "==> Checking podman..."
if ! command -v podman &> /dev/null; then
    echo "Podman not installed. Please install manually (sudo apt-get -y install podman) and rerun srcipt."
    exit 1
fi
echo "podman available ✔"

# podman pull debian:13-slim # Почему-то напрямую в build не работает.

# make build


IMAGE_ARCHIVE="data/bulls-pipeline.tar.gz"
IMAGE_NAME="bulls-pipeline"

# Проверяем, существует ли архив образа
if [ -f "$IMAGE_ARCHIVE" ]; then
    echo "📦 Archive $IMAGE_ARCHIVE found. Loading image..."
    if gunzip -c "$IMAGE_ARCHIVE" | podman load; then
        echo "✅ Image $IMAGE_NAME loaded successfully from archive."
    else
        echo "❌ Failed to load image from archive. Will attempt to build."
        NEED_BUILD=true
    fi
else
    echo "📦 Archive $IMAGE_ARCHIVE not found. Will build image from scratch."
    NEED_BUILD=true
fi

# Если образ не был загружен (или архива нет), собираем и сохраняем
if [ "${NEED_BUILD:-false}" = true ]; then
    echo "==> Building container image..."
    podman pull debian:13-slim   # если нужен свежий базовый образ
    make build
fi

echo "==> Done ✔"
