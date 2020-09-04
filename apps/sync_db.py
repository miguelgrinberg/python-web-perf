import os
import psycopg2
import psycopg2.pool
import random

if os.getenv('USE_MEINHELD'):
    from meinheld_psycopg2 import patch_psycopg
    patch_psycopg()
elif os.getenv('USE_GEVENT'):
    from psycogreen.gevent import patch_psycopg
    patch_psycopg()

max_n = 1000_000 - 1


def get_row():
    conn = psycopg2.connect(dbname='test', user='test', password='test',
                            port=5432, host='perf-dbpool')
    cursor = conn.cursor()
    index = random.randint(1, max_n)
    cursor.execute("select a, b from test where a = %s;", (index,))
    #cursor.execute("select pg_sleep(0.01); select a, b from test where a = %s;", (index,))
    ((a, b),) = cursor.fetchall()
    cursor.close()
    conn.commit()
    conn.close()
    return a, b
