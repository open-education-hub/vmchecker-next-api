# VMChecker Next API

The VMChecker API is built on [Django](https://www.djangoproject.com/). The project is made up of two parts, the API that exposes the URLs for Moodle, and a second process, that submits assignments to Gitlab, polls for the result or retrieves the output/assignment archive. It uses the Postgres database as a task queue.

## Requirements

1. `python3 >= 3.10`
2. `pipenv` (`pip3 install pipenv --user`. See [docs](https://pipenv.pypa.io/en/latest/installation.html))
3. `docker` (See official docker [docs](https://docs.docker.com/engine/install/))
4. Create a test assignment on [Gitlab.com](https://gitlab.com/) by following the [TA handbook](https://github.com/open-education-hub/vmchecker-next/wiki/Teaching-Assistant-Handbook). You will only require the private git repository. You can directly fork the following [template assignment](https://gitlab.cs.pub.ro/vmchecker/vmchecker-next-assignment).

### Setting up the development environment

1. After cloning the repository install the python packages using `pipenv install`.
2. Clone the Vmchecker Moodle plugin from: [VMChecker Next](https://github.com/open-education-hub/vmchecker-next) and change the compose-dev moodle service's path to point to it
3. Start the environment using `./bin/dev.sh up --watch`

#### First time configuration:

**Note**: The first time you run `dev.sh` the moodle service might fail. Comment out the vmchecker volume bind and do `dev.sh down && dev.sh up --watch`.

If this is the first time starting up the development environment you'll have to set up a Moodle assignment and configure the Moodle plugin.

To configure the Moodle block plugin:

1. Go to `Site Administration > Plugins > Blocks > VMChecker block`
2. Change `vmck backend` to `http://backend:8000/api/v1/`

To set up the Moodle assignment create a [course](https://docs.moodle.org/405/en/Create_a_course) and some [users](https://docs.moodle.org/405/en/Create_a_user) and [add them to the course](https://docs.moodle.org/405/en/Add_new_users). Then you can follow the [TA handbook](https://github.com/open-education-hub/vmchecker-next/wiki/Teaching-Assistant-Handbook) on how to prepare the assignment.

**Useful notes**:
- Moodle is avaialbe at `http://localhost/`
    - User: `admin`, Password: `Parola-123`
    - If you are also developing the Moodle plugin check out the [Moodle debugging notes](https://docs.moodle.org/405/en/Debugging)
- VMChecker service port `8000`

### Debugging

The backend service exposes port `5678` for debugging. A VS Code configuration example:
```json
{
            "name": "Python Debugger: Remote Attach",
            "type": "debugpy",
            "request": "attach",
            "connect": {
                "host": "localhost",
                "port": 5678
            },
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}",
                    "remoteRoot": "/opt/api"
                }
            ]
        }
```

### Running tests

`pipenv run pytest test/`
