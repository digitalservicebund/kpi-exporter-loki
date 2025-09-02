FROM python:3.13.6-alpine3.22

ENV LOKI_VERSION 3.4.0

RUN apk update \
 && apk add --no-cache jq coreutils \
 && rm -rf /var/cache/apk/* \
 && wget https://github.com/grafana/loki/releases/download/v"${LOKI_VERSION}"/logcli-linux-amd64.zip \
 && unzip logcli-linux-amd64.zip \
 && pip install --no-cache-dir requests pyyaml

WORKDIR /app

COPY query_and_submit.py .

CMD ["python", "./query_and_submit.py"]
