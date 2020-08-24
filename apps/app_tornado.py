import asyncio
import json
import os
import uvloop
import tornado.ioloop
import tornado.web
from async_db import get_row


class Handler(tornado.web.RequestHandler):
    async def get(self):
        a, b = await get_row()
        self.write(json.dumps({"a": str(a).zfill(10), "b": b}))


def make_app():
    return tornado.web.Application([
        (r"/test", Handler),
    ])


if __name__ == "__main__":
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    app = make_app()
    server = tornado.httpserver.HTTPServer(app)
    server.bind(8001)
    server.start(int(os.environ.get('PWPWORKERS', '1')))
    tornado.ioloop.IOLoop.current().start()
