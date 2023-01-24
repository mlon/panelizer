FROM python:3.10

ENV PYTHONUNBUFFERED True

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

COPY fonts/Jost-600-Semi.otf /usr/local/share/fonts/
RUN fc-cache -fv

WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt 

COPY wsgi.py .
COPY panelizer panelizer
RUN pysassc panelizer/static/scss/style.scss panelizer/static/css/style.scss.css 
COPY symbols symbols

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 wsgi:app