#!/usr/bin/env python3
import json
from glob import glob

import bitmath


def read_requirements():
    reqs = {}
    with open('runs/requirements.txt') as f:
        for line in f.readlines():
            if ' @ ' in line:
                pkg = line.strip().split(' @ ')[0]
                version = line.strip().split('@')[-1][:7]
            else:
                pkg, version = line.strip().split('==')
            reqs[pkg.lower()] = (pkg, version)
    return reqs


def gen_report(reqs):
    report = []
    for test in glob('runs/*.json'):
        deps = [dep for dep in test[5:-5].split('-') if dep in reqs]
        workers = int(test.split('-x')[1].split('.')[0])
        if len(deps) == 1:
            deps = [deps[0], deps[0]]
        try:
            with open(test) as f:
                results = json.loads(f.read())
        except:
            continue
        with open(test.replace('.json', '.db')) as f:
            db_connections = int(f.read().strip())
        with open(test.replace('.json', '.perf')) as f:
            f.readline()
            cpu = 0
            ram = 0
            net_in = 0
            net_out = 0
            pids = 0
            for line in f.readlines():
                c, r, n, b, p = line.strip().split(',')
                c = float(c.split('%')[0])
                r = float(str(bitmath.parse_string(r.split(' / ')[0]).to_MB()).split()[0])
                n = [float(str(bitmath.parse_string(nn).to_MB()).split()[0])
                     for nn in n.split(' / ')]
                p = int(p)
                cpu = max(cpu, c)
                ram = max(ram, r)
                net_in = max(net_in, n[0])
                net_out = max(net_out, n[1])
                pids = max(pids, p)
        report.append([
            f'{reqs[deps[-1]][0]} {reqs[deps[-1]][1]}',
            ' with '.join([f'{reqs[dep][0]} {reqs[dep][1]}'
                           for dep in deps[:-1]]),
            workers,
            results['requests_per_second'],
            results['percentages']['50%'],
            results['percentages']['99%'],
            db_connections,
            int(results['complete_requests']),
            int(results.get('non-2xx_responses', 0)),
            cpu,
            ram,
            net_in,
            net_out,
            pids,
        ])
    report = sorted(report, key=lambda r: r[3], reverse=True)
    report.insert(0, [
        'framework',
        'server',
        'workers',
        'reqs/sec',
        'P50',
        'P99',
        'db_sessions',
        'total_reqs',
        'failed_reqs',
        'cpu_%',
        'ram_mb',
        'net_in_mb',
        'net_out_mb',
        'pids',
    ])
    return report


report = gen_report(read_requirements())
for line in report:
    print(','.join([v.__str__() for v in line]))
