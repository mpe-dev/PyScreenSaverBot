from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("screensaver_app", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AppLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("timestamp", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "level",
                    models.CharField(
                        choices=[
                            ("DEBUG", "Debug"),
                            ("INFO", "Info"),
                            ("WARNING", "Warning"),
                            ("ERROR", "Error"),
                            ("CRITICAL", "Critical"),
                        ],
                        db_index=True,
                        max_length=10,
                    ),
                ),
                ("logger_name", models.CharField(db_index=True, max_length=200)),
                ("message", models.TextField()),
            ],
            options={
                "verbose_name": "Log Entry",
                "verbose_name_plural": "Log Entries",
                "ordering": ["-timestamp"],
            },
        ),
    ]
