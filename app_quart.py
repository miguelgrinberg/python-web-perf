from os import environ

from quart import Quart, jsonify
from async_db import get_row

app = Quart("python-web-perf")


@app.route("/test")
async def test():
    a, b = await get_row()
    return jsonify({"a": str(a).zfill(10), "b": b})
