# VMChecker Next API

The VMChecker API is built on [Django](https://www.djangoproject.com/). The project is made up of two parts, the API that exposes the URLs for Moodle, and a second process, that submits assignments to Gitlab, polls for the result or retrieves the output/assignment archive. It uses the Postgres database as a task queue.

## Requirements

1. `python3 >= 3.8`
2. `pipenv` (`pip3 install pipenv --user`. See [docs](https://pipenv.pypa.io/en/latest/installation.html))
3. `docker` (See official docker [docs](https://docs.docker.com/engine/install/))
4. A Moodle installation with the vmchecker plugin installed. See the vmchecker-next [docs](https://github.com/open-education-hub/vmchecker-next/blob/master/CONTRIBUTING.md#requirements) on how to set up a development environment. If you do not plan on working on the Moodle plugin, follow the following workshop tutorial on setting up a Moodle instance with the vmchecker plugin installed ([Tutorial](https://open-education-hub.github.io/docs/events/vmchecker-workshop/vmchecker-moodle-install)).
5. Create a test assignment on [Gitlab.com](https://gitlab.com/) by following the [TA handbook](https://github.com/open-education-hub/vmchecker-next/wiki/Teaching-Assistant-Handbook). You will only require the private git repository. You can directly fork the following [template assignment](https://gitlab.cs.pub.ro/vmchecker/vmchecker-next-assignment).

### Setting up the development environment

1. After cloning the repository install the python packages using `pipenv install`.
2. `cp ./etc/.env.development .env`
3. Customize the `.env` file with the correct information
4. Start up the development stack `pipenv run docker-compose-dev up`. It will start a `Minio` and `Postgres` instance under the 'api' namespace

### Running tests

`pipenv run pytest test/`
