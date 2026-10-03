FROM python:3.13-slim

WORKDIR /app
COPY app.py .

RUN useradd --uid 10001 --no-create-home appuser
USER 10001

ENV APP_HOST=0.0.0.0 \
    APP_PORT=8080 \
    PYTHONUNBUFFERED=1

EXPOSE 8080
CMD ["python", "app.py"]
