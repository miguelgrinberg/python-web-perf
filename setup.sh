#!/bin/bash -ex

# configuration variables
REPO_USER=miguelgrinberg
REPO_NAME=python-web-perf
REPO_BRANCH=master
DB_NAME=test
DB_USER=test
DB_PASSWORD=test
DB_TABLE=test

# dependencies
apt-get update
apt-get install -y build-essential git postgresql pgbouncer python3-dev python3-venv nginx apache2-utils

# test repository
if [[ ! -d $REPO_NAME ]]; then
	git clone https://github.com/$REPO_USER/$REPO_NAME.git
fi
cd $REPO_NAME
git checkout $REPO_BRANCH

# nginx
sed -i "s/worker_connections [0-9]*;/worker_connections 20000;/" /etc/nginx/nginx.conf
cp nginx.conf /etc/nginx/sites-available/perf
rm /etc/nginx/sites-enabled/*
ln -s /etc/nginx/sites-available/perf /etc/nginx/sites-enabled/
systemctl reload nginx

# python
if [[ ! -d venv ]]; then
	python3 -m venv venv
fi
venv/bin/pip install -r requirements.txt

# database
cp pgbouncer/* /etc/pgbouncer/
systemctl restart pgbouncer
if [[ ! -f data.csv ]]; then
	./gen_test_data.py > data.csv
fi
su -c "psql -c \"DROP DATABASE IF EXISTS $DB_NAME;\"" postgres
su -c "psql -c \"CREATE DATABASE $DB_NAME;\"" postgres
su -c "psql -c \"DROP USER IF EXISTS $DB_USER; CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';\"" postgres
#su -c "psql -c \"GRANT ALL ON DATABASE $DB_NAME TO $DB_USER;\"" postgres
su -c "psql test < schema.sql" postgres
su -c "psql test -c \"COPY test FROM '$PWD/data.csv' DELIMITER ',' CSV HEADER;\"" postgres
su -c "psql test -c \"GRANT ALL ON TABLE $DB_TABLE TO $DB_USER;\"" postgres
