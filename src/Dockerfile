FROM python:3.10-alpine

WORKDIR /app
COPY . .
RUN mkdir -p common
RUN mkdir -p assets
RUN mkdir -p log

ARG REQUIREMENT_FILE="requirements.py"

COPY common/tools.py common
COPY assets/* assets

RUN \
 apk add --no-cache postgresql-libs && \
 apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev && \
 python3 -m pip install -r $REQUIREMENT_FILE --no-cache-dir && \
 apk --purge del .build-deps

ENTRYPOINT ["python"]
CMD ["app.py"]