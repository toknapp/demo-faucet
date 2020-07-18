FROM python:3.7.4-alpine3.10

RUN apk add --no-cache --virtual build-deps build-base
RUN apk add libffi-dev openssl-dev

RUN adduser --disabled-password --gecos '' --home /faucet faucet

USER faucet
RUN python3 -m venv /faucet/env
RUN /faucet/env/bin/pip install --upgrade pip setuptools

ENV PATH /faucet/env/bin:$PATH

COPY --chown=faucet:faucet requirements /faucet/requirements
RUN pip install -r /faucet/requirements/requirements.txt
RUN rm -r /faucet/requirements && mkdir /faucet/static

USER root
RUN apk del build-deps

USER faucet

ENV UPVEST_USER_AGENT="upvest-faucet/docker"

COPY --chown=faucet:faucet faucet /faucet/app
WORKDIR /faucet/app
COPY --chown=faucet:faucet entrypoint.sh /faucet/entrypoint.sh
CMD ["sh", "/faucet/entrypoint.sh"]
