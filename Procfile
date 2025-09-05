web: gunicorn bookscart.wsgi:application --log-file - 
web: python manage.py migrate && gunicorn bookscart.wsgi