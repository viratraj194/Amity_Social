# Generated by Django 5.0.6 on 2024-07-12 06:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('list_posts', '0003_alter_userposts_options'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userposts',
            name='post_video',
        ),
    ]
