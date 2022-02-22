from __future__ import annotations
from typing import Union
from enum import Enum

from django.db import models
from django.utils import timezone


class TaskState(str, Enum):
    new = '0'
    waiting_for_results = '1'
    done = '2'
    error = '3'

    @staticmethod
    def from_name(name: str) -> Union[TaskState, None]:
        for enum in TaskState:
            if enum.name == name:
                return enum
        return None


class Task(models.Model):
    submission_data_id = models.CharField(max_length=40, blank=False)
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
    error_info = models.CharField(max_length=2048, blank=True)
    updated_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        return super(Task, self).save(*args, **kwargs)
