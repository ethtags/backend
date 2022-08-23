release: cd ./tagmi && python manage.py migrate
web: gunicorn --pythonpath ./tagmi/ tagmi.wsgi
worker: cd ./tagmi && python manage.py heroku-worker
