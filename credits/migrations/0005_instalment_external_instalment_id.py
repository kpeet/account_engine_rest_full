# Generated by Django 2.1.5 on 2019-05-15 22:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('credits', '0004_auto_20190513_1903'),
    ]

    operations = [
        migrations.AddField(
            model_name='instalment',
            name='external_instalment_id',
            field=models.IntegerField(default=None, unique=True),
        ),
    ]
