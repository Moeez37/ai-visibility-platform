FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV FLASK_APP=wsgi.py
EXPOSE 5000

# One worker: the pipeline runs on a background thread inside the process.
CMD ["sh", "-c", "flask db upgrade && gunicorn --bind 0.0.0.0:5000 --workers 1 --threads 8 --timeout 180 wsgi:app"]
