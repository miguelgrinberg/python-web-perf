from aioflask import Flask
from async_db import get_row

app = Flask("python-web-perf")


@app.route("/test")
async def test():
    a, b = await get_row()
    return {"a": str(a).zfill(10), "b": b}
