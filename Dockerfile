FROM python:3.11.13-slim
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev \
    && rm -rf /var/lib/apt/lists/*
RUN adduser --disabled-password --gecos "" appuser
COPY . /app
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt
USER appuser
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "warning"]
