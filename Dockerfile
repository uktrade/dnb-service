FROM python:3.12.10

RUN apt-get update && apt-get install -y wget

# Install dockerize https://github.com/jwilder/dockerize
ENV DOCKERIZE_VERSION v0.9.3
RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz

EXPOSE 8000

RUN mkdir -p /app
WORKDIR /app

ADD requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

ADD . /app/

CMD ./start_docker.sh
