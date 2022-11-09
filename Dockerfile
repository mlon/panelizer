FROM python:3.10

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

WORKDIR /workspace
COPY requirements.txt .

RUN pip install -r requirements.txt 

COPY symbols symbols
COPY panelizer panelizer
COPY pyproject.toml .
RUN pip install .

WORKDIR /data
ENTRYPOINT ["python3", "-m"]