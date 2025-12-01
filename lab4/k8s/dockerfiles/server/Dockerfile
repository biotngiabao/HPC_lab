FROM lab4-base:latest

WORKDIR /app/server
# Copy server code from build context
COPY server/ /app/server

ENV PYTHONUNBUFFERED=1
CMD ["python", "main.py"]
