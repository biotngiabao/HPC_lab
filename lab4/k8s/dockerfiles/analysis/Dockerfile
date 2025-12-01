FROM lab4-base:latest

WORKDIR /app/analysis
# Copy analysis code from build context
COPY analysis/ /app/analysis

ENV PYTHONUNBUFFERED=1
CMD ["python", "main.py"]
