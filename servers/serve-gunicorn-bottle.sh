#!/usr/bin/env bash

gunicorn --bind :8001 -w $PWPWORKERS app_bottle:app
