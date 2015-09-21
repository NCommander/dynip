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
    _networks = { }

    def __init__(self, db_info_dict):
        '''Opens a connection to the MySQL database'''
        self.db_info = db_info_dict
        self.mysql_pool = mysql.connector.pooling.MySQLConnectionPool(pool_name = "datastore_pool",
                                                                     pool_size=20,
                                                                     **self.db_info)

        #self._refresh_network_topogoly()

    def create_machine(self, name, token):
        '''Creates a machine in the database'''
        cnx = self.mysql_pool.get_connection()
        cursor = cnx.cursor()
        query = '''INSERT INTO machine_info (name, token) VALUES (%s, %s)'''
        cursor.execute(query, (name, token))
        cnx.commit()
        cnx.close()

    def get_machine(self, name):
        '''Retrieves a machine from the database'''
        cnx = self.mysql_pool.get_connection()
        cursor = cnx.cursor(dictionary=True)
        query = '''SELECT * FROM machine_info WHERE name=%s'''
        cursor.execute(query, (name,))
        machine_dict = cursor.fetchone()
        cnx.close()

        return machine_dict

    def create_network(self, name, location, family, network, allocation_size, reserved_blocks):
        # pylint: disable=too-many-arguments
        '''Creates a network in the database'''

        # Argument validation
        check.is_valid_ip_family(family)
        network = check.validate_and_normalize_ip_network(network)
        check.is_valid_prefix_size(allocation_size, family)

        # FIXME: make sure we're not trying to add ourselves twice

        cnx = self.mysql_pool.get_connection()
        cursor = cnx.cursor()
        query = '''INSERT INTO network_topology (name, location, family, network, allocation_size,
                                                 reserved_blocks) VALUES (%s, %s, %s,%s, %s, %s)'''

        cursor.execute(query, (name, location, int(family), network, allocation_size,
                               reserved_blocks))
        cnx.commit()
        cnx.close()

        # Update our state information to see the new network
        self.refresh_network_topogoly()

    def assign_allocation(self, machine, network, allocation):
        '''Assigns an from a machine to an allocation to a machine'''

    def get_networks(self):
        '''Returns a list of networks'''

        network_list = []
        # We don't want to return the internal dict because someone might do something stupid with
        # it, especially because it exposes the id number. So build a list and return that

        for network in self._networks.values():
            network_list.append(network)

        return network_list

    def refresh_network_topogoly(self):
        '''Updates the network topology in the database'''

        # Setup the connection, and cursor
        cnx = self.mysql_pool.get_connection()
        cursor = cnx.cursor(dictionary=True)

        # Pull the entire topology from the database
        query = "SELECT * FROM network_topology ORDER BY id"
        cursor.execute(query)

        for row in cursor:
            self._networks[row['id']] = NetworkBlock(row, self)

        cnx.close()

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
