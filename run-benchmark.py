import os
import re
import signal
import subprocess
import time
import requests

BENCHMARKS = [
    ('gunicorn-flask', 16),
    ('gunicorn-gevent-flask', 1),
    ('gunicorn-meinheld-bottle', 1),
    ('gunicorn-meinheld-falcon', 1),
    ('gunicorn-meinheld-flask', 1),
    ('uwsgi-bottle', 16),
    ('uwsgi-bottle-own-proto', 16),
    ('uwsgi-falcon', 16),
    ('uwsgi-flask', 16),
    ('aiohttp', 1),
    ('daphne-starlette', 1),
    ('sanic-own', 1),
    ('uvicorn-quart', 1),
    ('uvicorn-sanic', 1),
    ('uvicorn-starlette', 1),
]
URL = "http://127.0.0.1:8000/test"
NSTART = 32
NITER = 2
NAVG = 3


def ab(clients, url):
    cmd = f'ab -c{clients} -n{clients * 10} {url}'
    output = subprocess.check_output(cmd.split(), stderr=subprocess.STDOUT)
    match = re.search(b'Requests per second:\\s+([0-9\\.]+)', output)
    return float(match.group(1))


def run_benchmark(benchmark):
    time.sleep(1)
    process = subprocess.Popen(f'bash serve-{benchmark}.sh',
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, shell=True,
                               preexec_fn=os.setsid)
    time.sleep(1)
    r = requests.get('http://localhost:8000/test')
    r.raise_for_status()

    count = NSTART
    results = []
    for i in range(NITER):
        print(f'{i+1}/{NITER}')
        reqsec = 0
        for j in range(NAVG):
            reqsec += ab(count, URL)
        reqsec = round(reqsec / NAVG)
        results.append(reqsec)
        count *= 2
    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    return results


results = {}
for benchmark, workers in BENCHMARKS:
    benchmark_name = f'{benchmark} x{workers}'
    print(benchmark_name)
    os.environ['PWPWORKERS'] = str(workers)
    results[benchmark_name] = run_benchmark(benchmark)

header = 'benchmark'
count = NSTART
for _ in range(NITER):
    header += f',{count}'
    count *= 2
print(header)
for benchmark, result in results.items():
    print(f'{benchmark},{",".join([str(r) for r in result])}')
