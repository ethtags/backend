# Generated by Django 4.0.6 on 2022-08-22 11:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nametags', '0002_tag_source'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tag',
            name='nametag',
            field=models.CharField(max_length=255),
        ),
    ]