FROM python:3.10
WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt
COPY src/*.py /app/
COPY src/*.sh /app/
