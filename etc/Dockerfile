FROM python:3.8.10-buster

RUN set -e \
 && pip install pipenv

WORKDIR /opt/api
COPY Pipfile Pipfile.lock ./
RUN pipenv install --system --deploy --ignore-pipfile

COPY manage.py ./
ADD api ./api
ADD bin ./bin
ADD etc ./etc
RUN ./manage.py collectstatic --no-input

VOLUME /opt/api/data
EXPOSE 8000
CMD ./bin/startapi.sh
