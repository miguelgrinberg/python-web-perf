# Python webserver performance comparison

Heavily based on [Cal Paterson's benchmark](https://github.com/calpaterson/python-web-perf), with some bugs fixed and some
new web servers and web frameworks added.

A description of this benchmark and some results are published in my article
[Ignore All Web Performance Benchmarks, Including This One](https://blog.miguelgrinberg.com/post/ignore-all-web-performance-benchmarks-including-this-one).

## Benchmark code

You can find the implementations of this benchmark for the different web
frameworks, as well as the startup commands for all web servers, in the `src`
directory.

## Running the benchmark

The `run-docker.sh` command creates containers for nginx, pgbouncer and
postgres and sets them up for the test. Then it builds a local image with all
the application code and server startup scripts. It finally runs each of the
tests in random order by starting a web server container and a load generator
container. To run one or more specific tests you can pass the test name(s) as
arguments. The list of available tests is in the file `tests.txt`.

Look at the top of `run-docker.sh` for the list of environment variables that
configure the test environment.
