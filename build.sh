#!/usr/bin/env bash
# execute on error
set -o errexit

# Install dependencies
python -m pip install --upgrade pip
pip install -r core/requirements.txt

# Migrate and collect static files
cd core
python manage.py collectstatic --noinput
python manage.py migrate
