#!/bin/bash

# exit on errors
set -euv

# delete old virtual environment if it exists
rm -rf .env || true

# create new virtual env
python3.10 -m venv .env

# activate virtual environment
set +v
source .env/bin/activate
set -v

# install project's python dependencies
pip install -r ./requirements.txt  --no-cache-dir

# check for .env file and use the template if it's not there
cd tagmi
[ -f ".env" ] || cp ./sample-dev-env ./.env

# run linter
pylint --load-plugins pylint_django --ignore-paths="nametags/migrations" --django-settings-module=tagmi.settings ./tagmi/ ./nametags/

# run flake8
flake8 --extend-exclude "migrations" ./

# run tests
python manage.py test

# run migrations
python manage.py migrate
