#!/bin/bash -e

[[ -z "$NUM_CLIENTS" ]] && NUM_CLIENTS=100
[[ -z "$NUM_CONNECTIONS" ]] && NUM_CONNECTIONS=100000
[[ -z "$NUM_WORKERS_SYNC" ]] && NUM_WORKERS_SYNC=16
[[ -z "$NUM_WORKERS_ASYNC" ]] && NUM_WORKERS_ASYNC=6

ALL_TESTS=$(cat tests.txt | shuf)

if [[ "$@" != "" ]]; then
    ALL_TESTS="$@"
fi

ALREADY_UP=
if [[ "$(docker-compose ps -q)" != "" ]]; then
    ALREADY_UP=1
fi

if [[ "$ALREADY_UP" == "" ]]; then
    if [[ ! -f data.csv ]]; then
        ./gen_test_data.py
    fi
    docker-compose up -d
    sleep 2
    docker-compose run --rm -e PGPASSWORD=test db psql -h perf-db -U test < schema.sql
    docker-compose run --rm -e PGPASSWORD=test db psql -h perf-db -U test -c "COPY test FROM '/tmp/data.csv' DELIMITER ',' CSV HEADER;"
fi

docker build -t perf-app .
mkdir -p runs
rm -f runs/*
docker run --rm perf-app pip freeze > runs/requirements.txt

for test in $ALL_TESTS; do
    if [[ -z "$NUM_WORKERS" ]]; then
        PWPWORKERS=$NUM_WORKERS_ASYNC
        if [[ "$test" == *gunicorn* || "$test" == *uwsgi* ]]; then
            if [[ "$test" != *meinheld* && "$test" != *gevent* ]]; then
                PWPWORKERS=$NUM_WORKERS_SYNC
            fi
        else
            PWPWORKERS=$NUM_WORKERS_ASYNC
        fi
    else
        PWPWORKERS=$NUM_WORKERS
    fi
    echo Running $test x$PWPWORKERS
    docker run --rm -d --name perf-app --network container:perf-server -e PWPWORKERS=$PWPWORKERS perf-app ./serve-$test.sh
    sleep 2
    ./monitor-app.sh $test-x$PWPWORKERS &
    MONITOR_PID=$!
    $(docker run --rm --name perf-test --network container:perf-server jordi/ab -c$NUM_CLIENTS -n$NUM_CONNECTIONS http://localhost:8000/test | python ab2json.py > runs/$test-x$PWPWORKERS.json)
    kill $MONITOR_PID
    docker rm -f perf-app
done

if [[ "$ALREADY_UP" == "" ]]; then
    docker-compose down -v
fi

./gen_report.py
