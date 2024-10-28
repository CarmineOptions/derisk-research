FROM nginx:stable-alpine

COPY ./fullchain.pem /etc/letsencrypt/live/the-boats.eu/
COPY ./privkey.pem /etc/letsencrypt/live/the-boats.eu/
COPY ./default.conf /etc/nginx/conf.d/default.conf
