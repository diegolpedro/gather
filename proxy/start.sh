#!/bin/sh

set -e

envsubst < /etc/nginx/default.conf > /etc/nginx/conf.d/default.conf

# start nginx with the dameon running in the foreground
nginx -g "daemon off;"