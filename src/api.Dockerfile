FROM python:3.10

WORKDIR /app
COPY . .
RUN mkdir -p common
RUN mkdir -p log

COPY common/tools.py common
# COPY api-requirements.txt .
RUN pip install -r api-requirements.txt

CMD ["python", "api.py"]