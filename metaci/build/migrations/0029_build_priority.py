# Generated by Django 2.2.5 on 2019-09-24 20:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("build", "0028_auto_20190613_1421")]

    operations = [
        migrations.AddField(
            model_name="build", name="priority", field=models.IntegerField(default=0)
        )
    ]
