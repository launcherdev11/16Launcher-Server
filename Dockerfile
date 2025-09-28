FROM python:3.12-alpine

# Установим необходимые пакеты для архивирования (tar) и работы с pip
RUN apk add --no-cache tar

# Скопируем скрипт в контейнер
COPY backup.py /backup.py
COPY .env /.env
COPY requirements.txt /requirements.txt

# Установим boto3
RUN pip install --no-cache-dir -r requirements.txt

# Запуск скрипта
ENTRYPOINT ["python", "-u", "/backup.py"]
