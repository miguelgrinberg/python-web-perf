#!/bin/bash -e

[[ -z "$NUM_CLIENTS" ]] && NUM_CLIENTS=100
[[ -z "$NUM_CONNECTIONS" ]] && NUM_CONNECTIONS=50000
[[ -z "$NUM_WORKERS_SYNC" ]] && NUM_WORKERS_SYNC=19
[[ -z "$NUM_WORKERS_ASYNC" ]] && NUM_WORKERS_ASYNC=6
[[ -z "$NUM_DB_SESSIONS" ]] && export NUM_DB_SESSIONS=100
[[ -z "$DB_SLEEP" ]] && DB_SLEEP=0.02
[[ -z "$WARMUP_SECONDS" ]] && WARMUP_SECONDS=10

ALL_TESTS=$(cat tests.txt | shuf)

if [[ "$@" != "" ]]; then
    ALL_TESTS="$@"
fi

ALREADY_UP=
if [[ "$(docker-compose ps -q)" != "" ]]; then
    ALREADY_UP=1
fi

# Uncomment to aid debugging:
# set -x

if [[ "$ALREADY_UP" == "" ]]; then
    if [[ ! -f data.csv ]]; then
        ./gen_test_data.py > data.csv
    fi
    NUM_DB_SESSIONS=$NUM_DB_SESSIONS docker-compose up -d
    sleep 2
    docker-compose run --rm -T -e PGPASSWORD=test dbpool psql -h perf-dbpool -U test < schema.sql
    docker-compose run --rm -e PGPASSWORD=test dbpool psql -h perf-dbpool -U test -c "COPY test FROM '/tmp/data.csv' DELIMITER ',' CSV HEADER;"
fi

docker build -t perf-app .
mkdir -p runs
rm -f runs/*
rm -f failed.txt
docker run --rm perf-app pip freeze > runs/requirements.txt

function finalize_test() {
    set +e
    kill $MONITOR_PID
    docker rm -f perf-app
    set -e
    DB_CONN=$(docker-compose run --rm -e PGPASSWORD=postgres db psql -h perf-dbpool -U postgres -P pager=off -c "show servers;" pgbouncer | wc -l)
    DB_CONN=$((DB_CONN-4))
    docker-compose run --rm -e PGPASSWORD=postgres db psql -h perf-dbpool -U postgres -c "kill test;" pgbouncer
    docker-compose run --rm -e PGPASSWORD=postgres db psql -h perf-dbpool -U postgres -c "resume test;" pgbouncer
    echo $DB_CONN > runs/$test-x$PWPWORKERS.db
}

function finalize_end() {
    if [[ "$ALREADY_UP" == "" ]]; then
        docker-compose down -v
    fi

    ./gen_report.py > test.csv
    cat test.csv
}

function interrupt_test() {
    finalize_test
    finalize_end
}

trap interrupt_test INT

LEN=$(c() { echo $#; }; c $ALL_TESTS)
COUNTER=0
for test in $ALL_TESTS; do
    COUNTER=$((COUNTER+1))
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
    echo Running $COUNTER/$LEN $test x$PWPWORKERS
    docker run --rm -d --name perf-app --network container:perf-server -e PWPWORKERS=$PWPWORKERS -e DB_SLEEP=$DB_SLEEP perf-app ./serve-$test.sh
    SKIP_TEST=
    WARMUP=0
    echo  # Print a blank line
    while true; do
        HTTP_STATUS=$(curl --silent -o /dev/null -w "%{http_code}" http://localhost:8000/test)
        CURL_STATUS=$?
        echo -n -e "\r\033[1A\033[0K"  # Clear previous line
        echo -n "Warming up (curl exit code $CURL_STATUS, HTTP status $HTTP_STATUS)"
        WARMUP=$((WARMUP+1))
        printf '%*s\n' $WARMUP | tr ' ' '.'
        if [[ $CURL_STATUS == 0 ]]; then
            if [[ $HTTP_STATUS == "200" ]]; then
                break
            fi
        fi
        if [[ $WARMUP -gt $WARMUP_SECONDS ]]; then
            echo "App failed to start, skipping test"
            SKIP_TEST=1
            echo $test >> failed.txt
            break
        fi
        sleep 1
    done
    if [[ "$SKIP_TEST" == "" ]]; then
        ./monitor-app.sh $test-x$PWPWORKERS &
        MONITOR_PID=$!
        $(docker run --rm --name perf-test --network container:perf-server --platform linux/amd64 jordi/ab -c$NUM_CLIENTS -n$NUM_CONNECTIONS http://localhost:8000/test | python3 ab2json.py > runs/$test-x$PWPWORKERS.json)
    fi
    finalize_test
done

finalize_end
