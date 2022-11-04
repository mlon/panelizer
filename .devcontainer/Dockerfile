ARG VARIANT="3.10-bullseye"
FROM mcr.microsoft.com/vscode/devcontainers/python:0-${VARIANT}

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    build-essential \
    cmake \
    libcairo2-dev \
    python3-dev \
    libpotrace-dev \
    libvips-dev \
    libcairo2 \
    libpango1.0-0 \
    libpangocairo-1.0-0 \
    libvips42

RUN fc-cache -fv

#COPY requirements.txt /tmp/pip-tmp/
#RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
#   && rm -rf /tmp/pip-tmp