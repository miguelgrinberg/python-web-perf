#!/bin/bash -ex

# configuration variables
export REPO_USER=miguelgrinberg
export REPO_NAME=python-web-perf
export REPO_BRANCH=master

# dependencies
sudo apt-get update
sudo apt-get install -y build-essential git postgresql python3-dev python3-venv nginx apache2-utils

# test repository
if [[ ! -d $REPO_NAME ]]; then
	git clone https://github.com/$REPO_USER/$REPO_NAME.git
fi
cd $REPO_NAME
git checkout $REPO_BRANCH

# python
if [[ ! -d venv ]]; then
	python3 -m venv venv
fi
venv/bin/pip install --upgrade pip wheel
venv/bin/pip install -r requirements.txt
if [[ ! -f data.csv ]]; then
	./gen_test_data.py > /tmp/data.csv
fi

sudo ./setup-admin.sh
