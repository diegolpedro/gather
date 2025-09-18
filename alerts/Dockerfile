FROM python:3.10-alpine

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src/ /app/

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8500"]
