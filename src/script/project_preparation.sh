#!/bin/bash
set -e

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

echo "==> Running data download script..."
DOWNLOAD_SCRIPT="src/script/download_data_huggingface.py"

if [ -f "$DOWNLOAD_SCRIPT" ]; then
    uv run python "$DOWNLOAD_SCRIPT"
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

make build

echo "==> Done ✔"
