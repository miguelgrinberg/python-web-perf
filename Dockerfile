FROM python:3.8
WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt
COPY apps/*.py /app/
COPY servers/*.sh /app/
