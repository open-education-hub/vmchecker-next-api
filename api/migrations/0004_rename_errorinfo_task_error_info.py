# Generated by Django 4.0.1 on 2022-01-25 12:10

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0003_task_errorinfo_alter_task_state"),
    ]

    operations = [
        migrations.RenameField(
            model_name="task",
            old_name="errorInfo",
            new_name="error_info",
        ),
    ]
