FROM python:3.12-slim
WORKDIR /app
COPY pipeline.py sample.csv /app/
RUN chmod 755 /app && chmod 644 /app/*
CMD ["sleep", "infinity"]
