# Generated by Django 5.1.7 on 2025-04-05 05:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("kitchen", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="induction",
            name="is_free_use",
            field=models.BooleanField(default=False, verbose_name="자유 사용"),
        ),
    ]
