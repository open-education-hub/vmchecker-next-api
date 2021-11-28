from rest_framework import serializers

from api.models import Task


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'submission_data_id',
            'gitlab_url',
            'gitlab_token',
            'gitlab_project_id',
            'gitlab_pipeline_id',
            'moodle_username',
            'state',
            'UUID',
        ]
