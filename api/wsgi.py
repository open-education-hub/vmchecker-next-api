import os

import uwsgidecorators
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')

application = get_wsgi_application()


@uwsgidecorators.postfork
def preload():
    from api.core.task_runner import Runner

    if os.getenv('API_TASK_RUNNER_ENABLED') == 'True':
        Runner.instance()
