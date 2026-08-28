FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt \
    && pip install --no-cache-dir gunicorn==23.0.0

COPY backend /app/backend
RUN install -m 0755 /app/backend/entrypoint.py /usr/local/bin/agua-entrypoint.py

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=20s CMD ["python", "-c", "import json, urllib.request; data=json.load(urllib.request.urlopen('http://127.0.0.1:8000/api/health/', timeout=5)); raise SystemExit(0 if data.get('ok') is not False else 1)"]

USER 1000:1000

ENTRYPOINT ["python", "/usr/local/bin/agua-entrypoint.py"]

CMD ["sh", "-c", "python backend/manage.py migrate --noinput && exec gunicorn --chdir backend dashboard_project.wsgi:application --bind 0.0.0.0:8000 --workers 2 --access-logfile - --error-logfile -"]
