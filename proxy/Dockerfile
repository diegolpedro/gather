FROM nginx:1.27.1-alpine

ENV APP_HOST=airflow-webserver
ENV APP_PORT=8080
ENV LISTEN_PORT=80

COPY ./start.sh /start.sh
RUN chmod +x /start.sh

RUN touch /etc/nginx/conf.d/https.conf

COPY ./nginx.conf /etc/nginx/
COPY ./https.conf /etc/nginx/
COPY ./streams.conf /etc/nginx/

ENTRYPOINT [ "sh", "-c", "./start.sh" ]
