from json import JSONEncoder
from enum import Enum

from django.db import models


class TaskState(str, Enum):
    new = '0'
    waiting_for_results = '1'
    done = '2'


class Task(models.Model):
    submission_data_id = models.CharField(max_length=40, blank=False)
    gitlab_url = models.CharField(max_length=256, blank=False)
    gitlab_token = models.CharField(max_length=256, blank=False)
    gitlab_project_id = models.BigIntegerField(blank=False)
    gitlab_pipeline_id = models.BigIntegerField(default=-1)
    moodle_username = models.CharField(max_length=256, blank=False)
    state = models.CharField(
        max_length=1,
        choices=[(tag, tag.value) for tag in TaskState],
        default=TaskState.new.value,
    )
    UUID = models.CharField(max_length=36, blank=False)
