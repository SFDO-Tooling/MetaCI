# Generated by Django 3.1.14 on 2022-02-24 16:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('release', '0021_auto_20210922_2102'),
    ]

    operations = [
        migrations.AlterField(
            model_name='releasecohort',
            name='status',
            field=models.CharField(choices=[('Active', 'Active'), ('Approved', 'Approved'), ('Canceled', 'Canceled'), ('Completed', 'Completed'), ('Planned', 'Planned')], default='Planned', max_length=9),
        ),
    ]



