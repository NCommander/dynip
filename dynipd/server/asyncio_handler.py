'''
Created on Sep 19, 2015

@author: mcasadevall
'''

import asyncio
from asyncio import futures

def test():
    return b'test\n'

def test2(autheticated):
    return b'test2\n'

protocol_verbs = {'TEST': test,
                  'TEST2': test2}

class AsyncServerHandler(object):
    def __init__(self, reader, writer, mysql_data_store):
        self.reader = reader
        self.writer = writer
        self.mysql_data_store = mysql_data_store
        self.loop = asyncio.get_event_loop()


    def run(self):
        pass

    @asyncio.coroutine
    def handle_inbound_connection(self):
        '''Handles connection and authetication state'''
        authetication = False

        print ('here')

        # If we can process connections, send OK code
        self.writer.write(b'200 Go Ahead\n')
        yield from self.writer.drain()

        while True:
            data = None
            try:
                data = yield from asyncio.wait_for(self.reader.readline(), 10.0)
            except futures.TimeoutError:
                # Client timed out
                self.writer.close()
                return

            if data is None:
                self.writer.close()
                return

            # Loose the newline, and figure out our verb
            command_line = str(data.decode()).rstrip()
            verb = str(command_line).split(sep=" ")

            command_function = None
            if verb[0] in protocol_verbs:
                command_function = protocol_verbs[verb[0]]

            # testing
            future1 = self.loop.run_in_executor(None, self.mysql_data_store.load_network_topogoly)
            yield from future1

            # Authetication is a special case
            if command_function == test2:
                authetication = True
                continue

            print (authetication)
            self.writer.write(command_function())
