#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e 

echo "Running migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Compressing CSS/JS..."
python manage.py compress --force

echo "Starting Daphne..."
daphne -b 0.0.0.0 -p $PORT amity_social_main.asgi:application