web: FLASK_APP=run.py flask db upgrade && gunicorn -w 1 -k gthread --threads 4 -b 0.0.0.0:${PORT} wsgi:app
