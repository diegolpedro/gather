FROM python:3.10

WORKDIR /app
COPY . .
RUN mkdir -p common
RUN mkdir -p log

COPY common/tools.py common
# COPY uphb-requirements.txt .
RUN pip install -r uphb-requirements.txt

CMD ["python", "uphb.py"]