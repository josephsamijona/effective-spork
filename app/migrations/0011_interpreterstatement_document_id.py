# Generated by Django 5.1.4 on 2025-02-17 05:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0010_interpreterstatement_interpreterservice"),
    ]

    operations = [
        migrations.AddField(
            model_name="interpreterstatement",
            name="document_id",
            field=models.CharField(blank=True, max_length=20, unique=True),
        ),
    ]
