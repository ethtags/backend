# Generated by Django 4.0.4 on 2022-05-07 00:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('pubkey', models.CharField(editable=False, max_length=42, primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nametag', models.CharField(max_length=60)),
                ('address', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='nametags.address')),
            ],
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.BooleanField(null=True)),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='nametags.tag')),
            ],
        ),
    ]
