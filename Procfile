web: python manage.py migrate && gunicorn --port=$PORT config.wsgi:application
celery_worker: celery -A config worker -l info
celery_beat: celery -A config beat -l info -S django
