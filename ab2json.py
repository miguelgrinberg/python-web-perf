#!/usr/bin/env python3
import json
import re
import sys


def parse_ab_output(output):
    results = {}
    for line in output.split('\n'):
        if line.startswith('This is ApacheBench'):
            results['version'] = \
                re.match(r'.*Version ([0-9\.]+)', line).group(1)
        else:
            m = re.match(r'(.*):\s+(.*)', line)
            if m:
                key = m.group(1).lower().replace(' ', '_')
                values = m.group(2).split()
                if key in ['connect', 'processing', 'waiting', 'total']:
                    if 'connection_times' not in results:
                        results['connection_times'] = {}
                    results['connection_times'][key] = {
                        'min': float(values[0]),
                        'mean': float(values[1]),
                        'sd': float(values[2]),
                        'median': float(values[3]),
                        'max': float(values[4]),
                    }
                else:
                    results[key] = float(re.match(r'[0-9\.]+', values[0]).group(0)) \
                        if values[0][0].isnumeric() else values[0]
            else:
                m = re.match(r'\s*([0-9]+%)\s+([0-9]+)', line)
                if m:
                    key = m.group(1)
                    value = int(m.group(2))
                    if 'percentages' not in results:
                        results['percentages'] = {}
                    results['percentages'][key] = value
    return results


print(json.dumps(parse_ab_output(sys.stdin.read()), indent=4))
