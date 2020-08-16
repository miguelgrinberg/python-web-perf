#!/usr/bin/env bash

hypercorn -b :8001 -w $PWPWORKERS app_quart:app
