FROM python:3.11
RUN apt-get update && apt-get install -y libpq-dev
RUN useradd -m appuser
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 8000
USER appuser
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
