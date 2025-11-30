FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY termai termai/

# Create a non-root user for security best practices
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser:appuser /app

USER appuser
CMD ["python", "-m", "termai"]
