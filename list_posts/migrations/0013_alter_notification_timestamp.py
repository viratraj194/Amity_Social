# Generated by Django 5.0.6 on 2024-07-17 18:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('list_posts', '0012_notification'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
