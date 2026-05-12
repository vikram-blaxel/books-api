FROM python:3.11
RUN apt-get update && apt-get install -y libpq-dev
RUN pip install --upgrade pip wheel
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
RUN useradd -m appuser
USER appuser
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
