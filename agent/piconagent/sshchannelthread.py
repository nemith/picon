import asyncio, asyncssh, sys, threading
import logging

class sshChannelThread(threading.Thread):
    def __init__(self,loop=asyncio.new_event_loop(),tunnelserver='localhost',tunnelport=2222):
        self.loop = loop
        super().__init__()
        self.tunnelserver=tunnelserver
        self.tunnelport=tunnelport
    def run(self):
        try:
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.run_client())
        except (OSError, asyncssh.Error) as exc:
            logging.critical('Failed to open SSH port forwarding channel: '+str(exc))

    @asyncio.coroutine
    def run_client(self):
        with (yield from asyncssh.connect(self.tunnelserver)) as conn:
            listener = yield from conn.forward_remote_port("", self.tunnelport, 'localhost', 22)
            yield from listener.wait_closed()
        yield from conn.wait_closed()


