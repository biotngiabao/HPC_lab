FROM lab4-base:latest

WORKDIR /app/client
# Copy client code from build context
COPY client/ /app/client

ENV PYTHONUNBUFFERED=1
CMD ["python", "main.py"]
