FROM python:3.13-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    fontconfig \
    libfreetype6-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/var/task
ENV FONTCONFIG_PATH=/etc/fonts
ENV AWS_LAMBDA_RUNTIME_API=""

WORKDIR /var/task

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir awslambdaric

ADD https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie /usr/local/bin/aws-lambda-rie
RUN chmod +x /usr/local/bin/aws-lambda-rie

COPY . .
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

RUN mkdir -p /tmp/certificates && \
    chmod 777 /tmp/certificates

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD [ "lambda_function.lambda_handler" ]
