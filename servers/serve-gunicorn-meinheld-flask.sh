#!/usr/bin/env bash

export USE_MEINHELD=1
gunicorn --bind :8001 -w $PWPWORKERS app_flask:app --worker-class "egg:meinheld#gunicorn_worker"
