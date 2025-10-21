FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5001

CMD ["python", "-u", "intents/intent_manager.py", "--cfg=./intents/config-gemini-docker.json"]
