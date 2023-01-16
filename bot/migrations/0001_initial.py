# Generated by Django 4.1.5 on 2023-01-15 23:31

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='data_api',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telegram_api', models.CharField(max_length=255)),
                ('openai_api', models.CharField(max_length=255)),
                ('chatId_telegram', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='scheduler',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Matkul', models.CharField(max_length=225)),
                ('Dateline', models.DateTimeField()),
                ('Keterangan', models.TextField()),
                ('Status', models.IntegerField(choices=[(1, 'SELESAI'), (0, 'TIDAK SELESAI')], default=0)),
            ],
        ),
    ]
