FROM python:3.9-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
# this is the port that Could Run is expecting
EXPOSE 8080
CMD ["python", "app.py"]
