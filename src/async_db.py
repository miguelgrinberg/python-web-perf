import os
import random
import aiopg

max_n = 1000_000 - 1
delay = float(os.getenv('DB_SLEEP', '0'))


async def get_row():
    async with aiopg.connect(dbname='test', user='test', password='test', port=5432, host='perf-dbpool') as conn:
        async with conn.cursor() as cursor:
            index = random.randint(1, max_n)
            await cursor.execute("select pg_sleep(%s); select a, b from test where a = %s", (delay, index))
            ((a, b),) = await cursor.fetchall()
    return a, b
