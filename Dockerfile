FROM python:3.12-slim

# Run as a non-root user (security best practice)
RUN useradd --create-home appuser
WORKDIR /home/appuser/app

COPY app.py .
USER appuser

CMD ["python", "app.py"]
