# Generated by Django 3.1.2 on 2020-10-03 18:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('groupme', '0001_initial_tables'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bot',
            name='group_id',
            field=models.CharField(db_index=True, max_length=32),
        ),
        migrations.AlterField(
            model_name='sauceruser',
            name='saucer_id',
            field=models.CharField(max_length=32),
        ),
        migrations.AlterField(
            model_name='user',
            name='access_token',
            field=models.CharField(max_length=64),
        ),
        migrations.AddIndex(
            model_name='historicalnickname',
            index=models.Index(fields=['group_id', 'groupme_id'], name='groupme_his_group_i_c90dae_idx'),
        ),
    ]
