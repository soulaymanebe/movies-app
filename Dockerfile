FROM python:3.11.13

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

CMD ["python", "app.py"]
