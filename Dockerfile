FROM python:3.10.12-buster

RUN set -e \
    && pip install pipenv

WORKDIR /opt/api
COPY Pipfile Pipfile.lock ./
RUN pipenv install --system --deploy --ignore-pipfile

COPY manage.py ./
ADD api ./api
ADD bin ./bin
ADD etc ./etc
RUN API_BUILD=1 ./manage.py collectstatic --no-input

EXPOSE 8000
CMD ./bin/startapi.sh
