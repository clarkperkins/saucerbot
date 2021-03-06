# Generated by Django 3.1.2 on 2020-10-03 20:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    replaces = [
        ('groupme', '0001_initial'),
        ('groupme', '0002_historicalnickname'),
        ('groupme', '0003_rename_sauceruser'),
        ('groupme', '0004_multiple_bots')
    ]

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SaucerUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('groupme_id', models.CharField(max_length=32, unique=True)),
                ('saucer_id', models.CharField(max_length=32, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='HistoricalNickname',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('groupme_id', models.CharField(max_length=32)),
                ('timestamp', models.DateTimeField()),
                ('nickname', models.CharField(max_length=256)),
                ('group_id', models.CharField(default=None, max_length=32)),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access_token', models.CharField(max_length=64, unique=True)),
                ('user_id', models.CharField(max_length=32, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Bot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bots', to='groupme.user')),
                ('bot_id', models.CharField(max_length=32)),
                ('group_id', models.CharField(max_length=32)),
                ('name', models.CharField(max_length=64)),
                ('slug', models.SlugField(max_length=64, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Handler',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('handler_name', models.CharField(max_length=64)),
                ('bot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='handlers', to='groupme.bot')),
            ],
        ),
    ]
