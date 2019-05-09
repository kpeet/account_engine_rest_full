# Generated by Django 2.1.5 on 2019-05-08 23:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account_engine', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='VirtualAccountDeposit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('bank_account_origin', models.OneToOneField(null=True, on_delete=django.db.models.deletion.PROTECT, to='account_engine.BankAccount')),
                ('journal', models.OneToOneField(null=True, on_delete=django.db.models.deletion.PROTECT, to='account_engine.Journal')),
                ('virtual_account_destiny', models.OneToOneField(null=True, on_delete=django.db.models.deletion.PROTECT, to='account_engine.Posting')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
