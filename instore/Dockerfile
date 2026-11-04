FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5001

# Default config file, kept in sync with the INSTORE_CONFIG default in docker-compose.yaml
ENV INSTORE_CONFIG=./intents/config-docker.json

CMD ["python", "-u", "intents/intent_manager.py"]
