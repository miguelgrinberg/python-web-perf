#!/bin/bash
echo CPUPerc,MemUsage,NetIO,BlockIO,PIDs >runs/$1.perf
while true; do
    docker stats --no-stream --format "{{.CPUPerc}},{{.MemUsage}},{{.NetIO}},{{.BlockIO}},{{.PIDs}}" perf-app >>runs/$1.perf
    sleep 3
done
