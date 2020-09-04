#!/usr/bin/env bash

export USE_MEINHELD=1
gunicorn --bind :8001 -w $PWPWORKERS app_falcon:app --worker-class "egg:meinheld#gunicorn_worker"
