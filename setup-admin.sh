#!/bin/bash -ex

# configuration variables
export DB_NAME=test
export DB_USER=test
export DB_PASSWORD=test
export DB_TABLE=test

# nginx
sed -i "s/worker_connections [0-9]*;/worker_connections 20000;/" /etc/nginx/nginx.conf
cp nginx.conf /etc/nginx/sites-available/perf
rm /etc/nginx/sites-enabled/*
ln -s /etc/nginx/sites-available/perf /etc/nginx/sites-enabled/
systemctl reload nginx

# database
cp pgbouncer/* /etc/pgbouncer/
systemctl restart pgbouncer
su -c "psql -c \"DROP DATABASE IF EXISTS $DB_NAME;\"" postgres
su -c "psql -c \"CREATE DATABASE $DB_NAME;\"" postgres
su -c "psql -c \"DROP USER IF EXISTS $DB_USER; CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';\"" postgres
#su -c "psql -c \"GRANT ALL ON DATABASE $DB_NAME TO $DB_USER;\"" postgres
su -c "psql test < schema.sql" postgres
su -c "psql test -c \"COPY test FROM '/tmp/data.csv' DELIMITER ',' CSV HEADER;\"" postgres
su -c "psql test -c \"GRANT ALL ON TABLE $DB_TABLE TO $DB_USER;\"" postgres
