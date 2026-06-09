FROM debian:13-slim

ENV DEBIAN_FRONTEND=noninteractive

# 1. Системные пакеты ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    git \
    ca-certificates \
    build-essential \
    # Сборочные зависимости для samtools/bcftools (они же покроют либы для REGENIE):
    zlib1g-dev \
    libbz2-dev \
    liblzma-dev \
    libcurl4-openssl-dev \
    libncurses-dev \
    # Рантайм для Java (Beagle):
    default-jre \
    # Рантайм для параллельных вычислений OpenMP (нужен REGENIE):
    libgomp1 \
    # ssh
    openssh-server \
    # dev - просмотр архивированных файлов, архивация и т.п
    less \
    zip \
    && rm -rf /var/lib/apt/lists/*


# 2. Настройка uv ----

# Фиксируем версию uv
COPY --from=ghcr.io/astral-sh/uv:0.11.16 /uv /uvx /bin/

WORKDIR /app

# Настройки uv
ENV UV_PYTHON=3.10 \
    UV_COMPILE_BYTECODE=0 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

# Установка Python-окружения по lock-файлу
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-install-project
ENV PATH="/opt/venv/bin:$PATH"

# 3. Сборка исходников ----
# 3.1 Копируем архивы исходников samtools/bcftools
COPY bin/bcftools-1.21.tar.bz2 bin/samtools-1.16.tar.bz2 /tmp/

# 3.2 Сборка bcftools
RUN tar --no-same-owner --no-same-permissions -xjvf /tmp/bcftools-1.21.tar.bz2 -C /tmp/ \
    && cd /tmp/bcftools-1.21 \
    && ./configure --prefix=/usr/local \
    && make -j$(nproc) && make install

# 3.3 Сборка samtools
RUN tar --no-same-owner --no-same-permissions -xjvf /tmp/samtools-1.16.tar.bz2 -C /tmp/ \
    && cd /tmp/samtools-1.16 \
    && ./configure --prefix=/usr/local \
    && make -j$(nproc) && make install \
    && rm -rf /tmp/*

# 3.4 Настройка путей для кастомных вызовов пайплайна
RUN mkdir -p /opt/tools/bin /opt/tools/samtools-1.16 \
    && ln -s /usr/local/bin/bcftools /opt/tools/bin/bcftools \
    && ln -s /usr/local/bin/samtools /opt/tools/samtools-1.16/samtools

# 3. Переменныые среды (ENV) ----
# Добавляем /app/bin в PATH, чтобы система видела regenie, magma, plink
ENV PATH="/app/bin:${PATH}"

# Русские символы внутри контейнера
#export LANG=C.UTF-8
#export LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

RUN echo 'export LANG=C.UTF-8' > /etc/profile.d/locale.sh && \
    echo 'export LC_ALL=C.UTF-8' >> /etc/profile.d/locale.sh
# 4. Настройка ssh ----
# Открытие ssh порта
EXPOSE 22

# Запуск ssh
CMD ["/usr/sbin/sshd", "-D", "-e"]
