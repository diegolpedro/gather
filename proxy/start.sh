#!/bin/sh

set -e

envsubst < /etc/nginx/https.conf > /etc/nginx/conf.d/https.conf

# start nginx with the dameon running in the foreground
nginx -g "daemon off;"
