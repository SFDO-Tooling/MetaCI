# Generated by Django 2.2.5 on 2019-09-25 19:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("plan", "0029_auto_20190905_2111")]

    operations = [
        migrations.AddField(
            model_name="plan", name="priority", field=models.IntegerField(default=0)
        )
    ]
