FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Dépendances minimales nécessaires pour exécuter Functions/GetProbas.py
COPY docker/requirements.getprobas.txt /tmp/requirements.getprobas.txt
RUN pip install -r /tmp/requirements.getprobas.txt

# Code (utile si tu veux aussi exécuter sans volume)
COPY . /app

CMD ["python", "-u", "Functions/GetProbas.py"]
