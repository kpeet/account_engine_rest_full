# Generated by Django 2.1.5 on 2019-05-09 14:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('account_engine', '0004_auto_20190509_0014'),
    ]

    operations = [
        migrations.CreateModel(
            name='BillingProperties',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('billable', models.BooleanField()),
                ('billing_entity', models.CharField(max_length=150, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CostAccountProperties',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('destination_account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='cost_account', to='account_engine.Account')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CreditsCost',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cost_amount', models.DecimalField(decimal_places=2, max_digits=20)),
                ('account_engine_properties', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='credits.CostAccountProperties')),
                ('billing_properties', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='credits.BillingProperties')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='InvestmentCreditOperation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('investment_id', models.IntegerField(unique=True)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=20)),
                ('investment_amount', models.DecimalField(decimal_places=2, max_digits=20)),
                ('credits_operation', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='account_engine.OperationAccount')),
                ('investment_cost', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='credits.CreditsCost')),
                ('investor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='investor', to='account_engine.Account')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
