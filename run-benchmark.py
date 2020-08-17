#!/usr/bin/env python
import os
import re
import signal
import subprocess
import sys
import time
import psutil
import requests

BENCHMARKS = [
    ('gunicorn-flask', 16),
    ('gunicorn-gevent-flask', 2),
    ('gunicorn-meinheld-bottle', 2),
    ('gunicorn-meinheld-falcon', 2),
    ('gunicorn-meinheld-flask', 2),
    ('uwsgi-bottle', 16),
    ('uwsgi-falcon', 16),
    ('uwsgi-flask', 16),
    ('aiohttp', 2),
    ('daphne-starlette', 2),
    ('hypercorn-quart', 2),
    ('sanic-own', 2),
    ('uvicorn-aioflask', 2),
    ('uvicorn-quart', 2),
    ('uvicorn-sanic', 2),
    ('uvicorn-starlette', 2),
]
URL = "http://127.0.0.1:8000/test"
NUM_CLIENTS = 100
NUM_CONNECTIONS = 10000

RAM_BASELINE = psutil.virtual_memory().available


def start_server(benchmark, workers):
    os.environ['PWPWORKERS'] = str(workers)
    process = subprocess.Popen(f'bash serve-{benchmark}.sh',
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, shell=True,
                               preexec_fn=os.setsid)
    time.sleep(1)
    return process


def stop_server(process):
    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    time.sleep(1)


def run_ab(clients, connections, url, name):
    cmd = f'ab -c{clients} -n{connections} {url}'
    try:
        output = subprocess.check_output(cmd.split(), stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        output = exc.output + b'\nExit code: ' + str(exc.returncode).encode(
            'utf-8')
        req = None
        cpu = None
        ram = None
    else:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory()
        ram = (RAM_BASELINE - ram.available) * 100 // ram.total
        match = re.search(b'Requests per second:\\s+([0-9\\.]+)', output)
        req = float(match.group(1))
    with open(f'tmp/{name}.txt', 'wt') as f:
        f.write(output.decode('utf-8'))
    return req, cpu, ram


def run_benchmark(benchmark_name):
    # first make sure the server is running
    r = requests.get('http://localhost:8000/test')
    if r.status_code != 200 or 'a' not in r.json() or 'b' not in r.json():
        return None, None, None
    return run_ab(NUM_CLIENTS, NUM_CONNECTIONS, URL, benchmark_name)


def run():
    psutil.cpu_percent()  # make first call to initialize metric
    benchmark = sys.argv[1] if len(sys.argv) > 1 else None
    results = {}
    if len(sys.argv) <= 1:
        for benchmark, workers in BENCHMARKS:
            benchmark_name = f'{benchmark}-x{workers}'
            print(benchmark_name)
            proc = start_server(benchmark, workers)
            results[benchmark_name] = run_benchmark(benchmark_name)
            stop_server(proc)
    else:
        for benchmark in sys.argv[1:]:
            proc = None
            if benchmark != '-':
                workers = None
                for b, w in BENCHMARKS:
                    if benchmark == b:
                        workers = w
                        break
                if workers is None:
                    raise RuntimeError(f'Benchmark {benchmark} is unknown.')
                proc = start_server(benchmark, workers)
                benchmark_name = f'{benchmark}-x{workers}'
            else:
                benchmark_name = f'current'
            print(benchmark_name)
            results[benchmark_name] = run_benchmark(benchmark)
            if proc:
                stop_server(proc)

    print('\nbenchmark,req,cpu,ram')
    for benchmark, results in results.items():
        print(f'{benchmark},{",".join([str(result) for result in results])}')


if __name__ == '__main__':
    run()
