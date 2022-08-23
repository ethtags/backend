release: cd ./tagmi && python manage.py migrate
web: gunicorn --pythonpath ./tagmi/ tagmi.wsgi
worker: python manage.py heroku-worker
