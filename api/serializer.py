from rest_framework import serializers

from api.models import Task


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "pk",
            "UUID",
            "moodle_username",
            "state",
            "gitlab_project_id",
            "gitlab_pipeline_id",
            "submission_data_id",
        ]
