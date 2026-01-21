FROM python:3.11-slim

WORKDIR /app

# Python Dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend Code
COPY backend ./backend

EXPOSE 8000

CMD ["python", "backend/main.py"]
