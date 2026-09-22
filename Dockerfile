FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py collector.py item_grants.py gm_commands.txt VERSION CHANGELOG.md ./
COPY templates ./templates
COPY static ./static
ENV PYTHONUNBUFFERED=1
EXPOSE 7789
CMD ["gunicorn", "--bind", "0.0.0.0:7789", "--workers", "2", "--threads", "4", "app:app"]
