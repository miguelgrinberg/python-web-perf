#!/usr/bin/env bash

export USE_GEVENT=1
gunicorn --bind :8001 -w $PWPWORKERS app_flask:app --worker-class gunicorn.workers.ggevent.GeventWorker
