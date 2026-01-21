FROM python:3.11-slim

WORKDIR /app

# Python Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend Code
COPY . .

EXPOSE 8000

CMD ["python", "main.py"]