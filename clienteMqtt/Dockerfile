FROM python:3.12

WORKDIR /app

ENV TZ="America/Argentina/Buenos_Aires"

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

ENV PYTHONUNBUFFERED=1

COPY . /app

CMD ["python", "/app/clienteMqtt.py"]