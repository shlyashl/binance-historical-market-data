FROM python:3.8-slim-buster

ARG PRJ=/usr/local/prj

ENV VIRTUAL_ENV=${PRJ}/venv
ENV PATH=${VIRTUAL_ENV}/bin:${PATH}

COPY requirements.txt ${PRJ}/

RUN set -ex \
    && buildDeps=' \
        freetds-dev \
        libkrb5-dev \
        libsasl2-dev \
        libssl-dev \
        libffi-dev \
    ' \
    && apt-get update -yqq \
    && apt-get upgrade -yqq \
    && apt-get install -yqq --no-install-recommends \
        $buildDeps \
        libpq-dev \
        freetds-bin \
        build-essential \
        default-libmysqlclient-dev \
        apt-utils \
        curl \
        rsync \
        netcat \
        locales \
    && useradd -ms /bin/bash -d ${PRJ} d_user \
    && python3 -m venv ${VIRTUAL_ENV} \
    && pip install -r ${PRJ}/requirements.txt \
    && apt-get purge --auto-remove -yqq $buildDeps \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf \
        /var/lib/apt/lists/* \
        /tmp/* \
        /var/tmp/* \
        /usr/share/man \
        /usr/share/doc \
        /usr/share/doc-base

COPY . ${PRJ}/
RUN chown -R d_user ${PRJ}

USER d_user
WORKDIR ${PRJ}
CMD [ "python", "main.py" ]
