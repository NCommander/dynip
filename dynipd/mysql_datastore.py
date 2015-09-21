'''
DynIPD - MySQL datastore for network configuration
Created on Sep 19, 2015

@author: mcasadevall
'''

import mysql.connector
from dynipd.network_block import NetworkBlock

class MySQLDataStore(object):
    '''Implements the data storage model on a MySQL database'''
    networks = { }

    def __init__(self, db_info_dict):
        '''Opens a connection to the MySQL database'''
        self.db_info = db_info_dict
        self.mysql_pool = mysql.connector.pooling.MySQLConnectionPool(pool_name = "datastore_pool",
                                                                     pool_size=20,
                                                                     **self.db_info)

        self._refresh_network_topogoly()

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
