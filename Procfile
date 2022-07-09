release: cd ./tagmi && python manage.py test && python manage.py migrate
web: gunicorn --pythonpath ./tagmi/ tagmi.wsgi
