# Użyj obrazu bazowego Python 3.12 slim
FROM python:3.12-slim

RUN apt-get update && apt-get install -y gosu

RUN groupadd -g 1000 appuser && useradd -u 1000 -g appuser -m appuser

# Ustaw katalog roboczy
WORKDIR /root

# Zainstaluj zależności systemowe
RUN apt-get update && apt-get install -y \
    sqlite3 \
    nodejs \
    npm \
    git \
    && rm -rf /var/lib/apt/lists/*

# Zaktualizuj pip do najnowszej wersji
RUN pip install --upgrade pip

# Skopiuj requirements.txt
COPY requirements.txt /app/requirements.txt

# Zainstaluj zależności Pythona
RUN pip install --no-cache-dir -r /app/requirements.txt

# Skopiuj resztę aplikacji
COPY . /app

# Ustaw katalog roboczy aplikacji
WORKDIR /app

ENTRYPOINT ["gosu", "1000:1000", "python3", "/app/generate_project.py"]

# Domyślne polecenie
CMD ["bash"]