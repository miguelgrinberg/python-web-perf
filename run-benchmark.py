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
    ('gunicorn-gevent-flask', 4),
    ('gunicorn-meinheld-bottle', 4),
    ('gunicorn-meinheld-falcon', 4),
    ('gunicorn-meinheld-flask', 4),
    ('uwsgi-bottle', 16),
    ('uwsgi-bottle-own-proto', 16),
    ('uwsgi-falcon', 16),
    ('uwsgi-flask', 16),
    ('aiohttp', 4),
    ('daphne-starlette', 4),
    ('hypercorn-quart', 4),
    ('sanic-own', 4),
    ('uvicorn-aioflask', 4),
    ('uvicorn-quart', 4),
    ('uvicorn-sanic', 4),
    ('uvicorn-starlette', 4),
]
URL = "http://127.0.0.1:8000/test"
NSTART = 32
NITER = 5
NAVG = 1

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


def run_ab(clients, url, name):
    cmd = f'ab -c{clients} -n{clients * 10} {url}'
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
        return [None] * NITER
    count = NSTART
    results = []
    for i in range(NITER):
        print(f'{i+1}/{NITER}')
        req = 0
        cpu = 0
        ram = 0
        for j in range(NAVG):
            _req, _cpu, _ram = run_ab(
                count, URL, f'{benchmark_name}-{count}' + '' if NAVG == 1 else f'-{j}')
            if _req is None:
                return [None] * NITER
            req += _req
            cpu += _cpu
            ram += _ram
        req = round(req / NAVG)
        cpu = round(cpu / NAVG)
        ram = round(ram / NAVG)
        results.append((req, cpu, ram))
        count *= 2
    return results


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

    header = 'benchmark'
    count = NSTART
    for _ in range(NITER):
        header += f',{count} connections'
        count *= 2
    print(header)
    for benchmark, result in results.items():
        print(f'{benchmark},{",".join([str(r) for r in result])}')


if __name__ == '__main__':
    run()
