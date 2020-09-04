import psycopg2
from psycopg2 import extensions

from meinheld import trampoline

def patch_psycopg():
    """Configure Psycopg to be used with eventlet in non-blocking way."""
    if not hasattr(extensions, 'set_wait_callback'):
        raise ImportError(
            "support for coroutines not available in this Psycopg version (%s)"
            % psycopg2.__version__)

    extensions.set_wait_callback(wait_callback)

def wait_callback(conn, timeout=-1):
    """A wait callback useful to allow eventlet to work with Psycopg."""
    while 1:
        state = conn.poll()
        if state == extensions.POLL_OK:
            break
        elif state == extensions.POLL_READ:
            trampoline(conn.fileno(), read=True)
        elif state == extensions.POLL_WRITE:
            trampoline(conn.fileno(), write=True)
        else:
            raise psycopg2.OperationalError(
                "Bad result from poll: %r" % state)
