# Generated by Django 5.0.6 on 2024-07-11 13:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('list_posts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userposts',
            name='post_slug',
            field=models.SlugField(blank=True, null=True, unique=True),
        ),
    ]
