web: FLASK_APP=run.py flask db upgrade && gunicorn -w 2 -k gthread --threads 4 --timeout 60 --access-logfile - -b 0.0.0.0:${PORT} wsgi:app
