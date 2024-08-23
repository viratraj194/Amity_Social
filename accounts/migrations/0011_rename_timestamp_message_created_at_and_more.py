# Generated by Django 5.0.6 on 2024-08-22 17:27

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_userprofile_is_privet'),
    ]

    operations = [
        migrations.RenameField(
            model_name='message',
            old_name='timestamp',
            new_name='created_at',
        ),
        migrations.AddField(
            model_name='message',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, db_index=True, max_length=255, null=True)),
                ('slug', models.SlugField(blank=True, null=True, unique=True)),
                ('is_private', models.BooleanField(db_index=True, default=False)),
                ('is_group', models.BooleanField(db_index=True, default=False)),
                ('description', models.TextField(blank=True, db_index=True, null=True)),
                ('room_picture', models.ImageField(blank=True, db_index=True, null=True, upload_to='room_pictures/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('creator', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_rooms', to=settings.AUTH_USER_MODEL)),
                ('participants', models.ManyToManyField(db_index=True, related_name='rooms', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
