FROM python:3.10-slim

WORKDIR /app

COPY employee/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p employee

COPY employee/ .

EXPOSE 5000

CMD ["python", "controller.py"]
