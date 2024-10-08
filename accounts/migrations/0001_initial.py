# Generated by Django 5.0.6 on 2024-08-01 17:12

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('first_name', models.CharField(max_length=50)),
                ('last_name', models.CharField(max_length=50)),
                ('gender', models.CharField(blank=True, max_length=20, null=True)),
                ('username', models.CharField(max_length=50, unique=True)),
                ('userSlug', models.SlugField(blank=True, max_length=100, unique=True)),
                ('email', models.EmailField(max_length=100, unique=True)),
                ('phone_number', models.CharField(blank=True, max_length=12)),
                ('collage_name', models.CharField(blank=True, null=True)),
                ('users_id', models.CharField(blank=True, max_length=20, null=True)),
                ('agree_to_terms', models.BooleanField(default=False)),
                ('is_approved', models.BooleanField(default=False)),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
                ('last_login', models.DateTimeField(auto_now_add=True)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('modified_date', models.DateTimeField(auto_now=True)),
                ('is_admin', models.BooleanField(default=False)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=False)),
                ('is_superadmin', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('profile_picture', models.ImageField(blank=True, height_field='image_height', null=True, upload_to='users/profile_picture', width_field='image_width')),
                ('image_width', models.PositiveIntegerField(blank=True, editable=False, null=True)),
                ('image_height', models.PositiveIntegerField(blank=True, editable=False, null=True)),
                ('cover_photo', models.ImageField(blank=True, height_field='cover_height', null=True, upload_to='users/cover_photo', width_field='cover_width')),
                ('cover_width', models.PositiveIntegerField(blank=True, editable=False, null=True)),
                ('cover_height', models.PositiveIntegerField(blank=True, editable=False, null=True)),
                ('collage_pin_code', models.CharField(blank=True, max_length=6, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
