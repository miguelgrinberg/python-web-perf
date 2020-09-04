#!/usr/bin/env bash

export USE_GEVENT=1
gunicorn --bind :8001 -w $PWPWORKERS app_falcon:app --worker-class gunicorn.workers.ggevent.GeventWorker
