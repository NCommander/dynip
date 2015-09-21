'''
DynIPD - MySQL datastore for network configuration
Created on Sep 19, 2015

@author: mcasadevall
'''

import mysql.connector
from dynipd.network_block import NetworkBlock
from dynipd.validation import ValidationAndNormlization as check

class MySQLDataStore(object):
    '''Implements the data storage model on a MySQL database'''
    networks = { }

    def __init__(self, db_info_dict):
        '''Opens a connection to the MySQL database'''
        self.db_info = db_info_dict
        self.mysql_pool = mysql.connector.pooling.MySQLConnectionPool(pool_name = "datastore_pool",
                                                                     pool_size=20,
                                                                     **self.db_info)

        #self._refresh_network_topogoly()

    # Helper for test code; used to load the schema into a test database
    def load_file_into_database(self, filename):
        #pylint: disable=unused-variable

        '''Reads a file and executes all queries in it. Meant for use by the testing API'''
        file = open(filename, mode='r')
        sql = file.read()
        file.close()

        # Setup the connection, and cursor
        cnx = self.mysql_pool.get_connection()
        cursor = cnx.cursor()
        result = cursor.execute(sql, multi=True)

        # We need to iterate on result to get it to execute; while loop just hangs
        for row in result: #@UnusedVariable
            pass
        cnx.close()

    def create_machine(self, name, token):
        '''Creates a machine in the database'''

    def create_network(self, name, location, protocol, network, allocation_size, reserved_blocks):
        # pylint: disable=too-many-arguments
        '''Creates a network in the database'''

        # Argument validation
        check.is_valid_ip_family(protocol)
        network = check.validate_and_normalize_ip_network(network)

        cnx = self.mysql_pool.get_connection()
        cursor = cnx.cursor()
        query = '''INSERT INTO network_topology VALUES (network_name=%s," .
                                                        location=%s,
                                                        protocol=%d,
                                                        network=%s,
                                                        allocation_size=%d,
                                                        reserved_blocks=%s)'''

        cursor.execute(query, (name, location, protocol, network, allocation_size,
                               reserved_blocks))
        cnx.close()

    def create_allocation(self, network_id, allocation):
        '''Creates an allocation for a machine'''
        cnx = self.mysql_pool.get_connection()
        cursor = cnx.cursor()

        cnx.close()

    def _refresh_network_topogoly(self):
        '''Gets the network topology from the database

        Returns a dict with each network stored in the database'''

        # Setup the connection, and cursor
        cnx = self.mysql_pool.get_connection()
        cursor = cnx.cursor(dictionary=True)

        # Pull the entire topology from the database
        query = "SELECT * FROM network_topology ORDER BY id"
        cursor.execute(query)

        for row in cursor:
            self.networks[row['id']] = NetworkBlock(row)

        cnx.close()
