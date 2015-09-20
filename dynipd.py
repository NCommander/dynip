# pylint: disable=no-name-in-module
'''
Created on Sep 19, 2015

@author: mcasadevall
'''

import asyncio
import argparse
import sys
import configparser
import socket
from dynipd.server.asyncio_handler import AsyncServerHandler
from dynipd.config_parser import ConfigurationParser
from dynipd.mysql_datastore import MySQLDataStore

# Ok, I think I'm loosing my mind, but when using start_server, there is no way that I can
# tell that one can pass in arguments to the callback function. Let me explain how this works
# and maybe someone can tell me a better way to do this.
#
# asyncio defines an event loop, which is essentially select() on network sockets. When a socket
# is opened to the server, it fires off begin_async_server on the event loop. The event loop
# works on the concept of cooperative multitasking (you know, like Windows 3.1, its 1993 again!),
# and calls a callback function each time a new socket is formed. Based off the API documentation
# there's no way to pass in a third argument, you just get the reader and writer objects and thats
# that. I'll explain why this is a problem in a moment.
#
# Anyway, the callback has to yield to allow the other sockets to be processed, and as long as
# everyone yields, we're in business. However, for a socket to do its job, it needs to be able
# to talk to the database to get the information required for processing. This requires either
# creating and tearing down a MySQL connection (which is very slow), or using a connection pool
#
# With me so far? Good. As best I can tell, looking at the source for mysql.connection, a pool
# exists as a single object. The same object has to be used by all members to get the advantage
# of the pool.
#
# Maybe you're seeing the problem now. Without a way to pass in addition arguments, there's no way
# to get the pool into the event loop! While there are ways to do this for threading (specifically
# creating a manager for your class), the event loop specifically operates on the concept of a
# single thread!
#
# What's even more confusing is there is a defined API for a coroutine (that's the unit of an async
# event loop) to fire off a thread and yield for it defined (this is the run_in_executor function).
#
# Thus, the only way to share an object between everyone is to define it as a global, and pass it
# in to the begin_async_server function. This (amazingly) works without throwing any sort of noise.
#
# As best I can tell, as long as I make calls to my class using the run_in_executor function,
# everything will basically work. mysql.connector says its thread-safe as long as a thread
# gets its own connection and only uses that (easy enough to enforce), but this feels like a
# giant hack to me. If anyone can provide any insight on the "right way" to do this, I'm all ears.


def async_initializer(datastore):
    '''Wrapper function for asnycio.start_server to grab the datastore object. See above'''
    def begin_async_server(reader, writer):
        '''Initialize the server handler, and away we go'''
        ash = AsyncServerHandler(reader, writer, datastore)
        yield from ash.handle_inbound_connection()
    return begin_async_server

def main():
    '''Starts dynipd server, and forks to background'''

    # Let's start with some basic environment setup. Argument parsing comes file
    parser_description = "DynIPD configuration daemon"
    parser = argparse.ArgumentParser(description=parser_description,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-c", "--config-file",
                        dest='filename',
                        help="Configuration file for dynipd",
                        metavar="FILE", default="/etc/dynipd.ini")
    args = parser.parse_args()

    # Make sure our config file is kosher
    cfg_file = None
    try:
        cfg_file = ConfigurationParser(args.filename)
    except FileNotFoundError:
        sys.stderr.write(("Configuration file %s not found. Bailing out!\n") % args.filename)
        sys.exit(-1)
    except configparser.MissingSectionHeaderError:
        sys.stderr.write("Configuration stanza is missing. Bailing out!\n")
        sys.exit(-1)

    # Initialize our data store; on initialization, it will pull
    # configuration settings like network topology
    datastore = MySQLDataStore(cfg_file.get_database_configuration())

    loop = asyncio.get_event_loop()
    # Each client connection will create a new protocol instance

    # For those not familiar with Python Socket programming, let me explain why we're
    # opening two sockets here. Under the defaults of *most* systems, opening an AF_INET6
    # socket will open both a v4 and v6 connection. This behavior is controlled by
    # IPV6_V6ONLY.
    #
    # However, the default setting for IPV6_V6ONLY is system defined, and not all operating
    # systems set it, and the default can also be overridden. To prevent having to debug
    # this later, we explicitly open two sockets, and enable IPV6_V6ONLY to prevent
    # a double bind on the v4 address.

    socket_v4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_IP)
    socket_v4.bind(('', 8888))

    socket_v6 = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, socket.IPPROTO_IP)
    socket_v6.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, True)
    socket_v6.bind(('', 8888))

    # Both sockets are set, run two server loops, one for v4 and another for v6
    coro_v4 = asyncio.start_server(async_initializer(datastore), None, None,
                                   loop=loop, sock=socket_v4)
    coro_v6 = asyncio.start_server(async_initializer(datastore), None, None,
                                   loop=loop, sock=socket_v6)
    server_v4 = loop.run_until_complete(coro_v4)
    server_v6 = loop.run_until_complete(coro_v6)

    # Serve requests until Ctrl+C is pressed
    print('Serving on {}'.format(server_v4.sockets[0].getsockname()))
    print('Serving on {}'.format(server_v6.sockets[0].getsockname()))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # Close the server
    server_v4.close()
    server_v6.close()
    loop.run_until_complete(server_v4.wait_closed())
    loop.run_until_complete(server_v6.wait_closed())
    loop.close()

main()
