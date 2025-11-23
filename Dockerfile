FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# اجرای Flask در حالت production
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0

EXPOSE 8000
CMD ["python", "app.py"]
