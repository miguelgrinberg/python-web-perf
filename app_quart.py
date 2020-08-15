from os import environ

from quart import Quart
from async_db import get_row

app = Quart("python-web-perf")


@app.route("/test")
async def test(request):
    a, b = await get_row()
    return {"a": str(a).zfill(10), "b": b}
