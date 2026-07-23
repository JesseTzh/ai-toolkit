ARG CUDA_IMAGE=nvidia/cuda:12.8.1-devel-ubuntu24.04
FROM ${CUDA_IMAGE}

LABEL authors="jaret"

ARG UBUNTU_MIRROR=https://mirrors.aliyun.com/ubuntu
ARG UBUNTU_PORTS_MIRROR=https://mirrors.aliyun.com/ubuntu-ports
ARG PYPI_INDEX_URL=https://mirrors.aliyun.com/pypi/simple
ARG PYTORCH_INDEX_URL=https://download.pytorch.org/whl/cu128
ARG NODE_MIRROR=https://npmmirror.com/mirrors/node
ARG NODE_VERSION=23.11.1
ARG NPM_REGISTRY=https://registry.npmmirror.com
ARG GITHUB_MIRROR_PREFIX=https://ghfast.top/https://github.com/

# Set noninteractive to avoid timezone prompts and use mainland China mirrors.
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_INDEX_URL=${PYPI_INDEX_URL}

# ref https://en.wikipedia.org/wiki/CUDA
ENV TORCH_CUDA_ARCH_LIST="8.0 8.6 8.9 9.0 10.0 12.0"

# Install dependencies
RUN sed -i -E \
        "s#https?://(archive|security).ubuntu.com/ubuntu/?#${UBUNTU_MIRROR}/#g; \
         s#https?://ports.ubuntu.com/ubuntu-ports/?#${UBUNTU_PORTS_MIRROR}/#g" \
        /etc/apt/sources.list.d/ubuntu.sources

RUN find /etc/apt/sources.list.d -type f ! -name ubuntu.sources \
        -exec sed -i -E '/^[[:space:]]*deb([[:space:]]|$)/s/^/# disabled for offline-friendly build: /' {} +

RUN apt-get update

RUN apt-get install --no-install-recommends -y \
    git \
    curl \
    build-essential \
    cmake \
    wget \
    python3.12 \
    python3-pip \
    python3-dev \
    python3-setuptools \
    python3-wheel \
    python3-venv \
    ffmpeg \
    tmux \
    htop \
    nvtop \
    python3-opencv \
    openssh-client \
    openssh-server \
    openssl \
    unzip \
    xz-utils

RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Node.js from npmmirror. The architecture mapping matches Node.js's
# binary archive naming for the platforms supported by the CUDA base image.
WORKDIR /tmp
RUN arch="$(dpkg --print-architecture)" && \
    case "${arch}" in \
        amd64) node_arch=x64 ;; \
        arm64) node_arch=arm64 ;; \
        *) echo "Unsupported architecture: ${arch}" >&2; exit 1 ;; \
    esac && \
    curl -fL "${NODE_MIRROR}/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-${node_arch}.tar.xz" \
        -o node.tar.xz && \
    tar -xJf node.tar.xz -C /usr/local --strip-components=1 && \
    rm node.tar.xz && \
    npm config set registry "${NPM_REGISTRY}"

WORKDIR /app

# Set aliases for python and pip
RUN ln -s /usr/bin/python3 /usr/bin/python

# Install PyTorch before application dependencies to maximize layer reuse.
RUN pip install --no-cache-dir torch==2.9.1 \
    --index-url "${PYTORCH_INDEX_URL}" --break-system-packages

RUN pip install --no-cache-dir torchvision==0.24.1 \
    --index-url "${PYTORCH_INDEX_URL}" --break-system-packages

RUN pip install --no-cache-dir torchaudio==2.9.1 \
    --index-url "${PYTORCH_INDEX_URL}" --break-system-packages

WORKDIR /app/ai-toolkit

# ---------------------------------------------------------------------------- #
# Dependency layers come BEFORE the source copy so they are only rebuilt (and
# only need to be re-pulled by servers) when the dependency manifests change,
# not on every code change.
# ---------------------------------------------------------------------------- #

# Install Python dependencies (only re-runs when the requirements files change)
COPY requirements.txt requirements_base.txt /app/ai-toolkit/
RUN git config --global \
        url."${GITHUB_MIRROR_PREFIX}".insteadOf "https://github.com/" && \
    pip install --no-cache-dir --break-system-packages -r requirements.txt && \
    pip install setuptools==69.5.1 --no-cache-dir --break-system-packages

# Install Node dependencies (only re-runs when package.json / package-lock.json change)
COPY ui/package.json ui/package-lock.json /app/ai-toolkit/ui/
RUN cd /app/ai-toolkit/ui && npm ci --registry="${NPM_REGISTRY}"

# ---------------------------------------------------------------------------- #
# Source code comes LAST. Only this layer (plus the UI build below) is rebuilt
# on a code change. .dockerignore keeps local dependencies and generated data
# out of the build context, so the node_modules installed above is preserved.
# ---------------------------------------------------------------------------- #
COPY . /app/ai-toolkit/

# Build UI (re-runs on code change, but reuses the cached node_modules above).
# update_db runs first because it does `prisma generate`, which creates the
# @prisma/client types the TS build needs. In the old layout generate happened
# as a side effect of npm install seeing the schema; now the source arrives
# after npm ci, so run it explicitly before the build.
RUN cd /app/ai-toolkit/ui && \
    npm run update_db && \
    npm run build

# Expose port (assuming the application runs on port 3000)
EXPOSE 8675

WORKDIR /

COPY docker/start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
