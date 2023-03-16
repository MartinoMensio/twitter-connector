FROM python:3.11-slim

COPY requirements.txt /app/
WORKDIR /app

RUN pip install -r requirements.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--workers", "4"]