'''
DynIPD - MySQL datastore for network configuration
Created on Sep 19, 2015

@author: mcasadevall
'''

import mysql.connector

class MySQLDataStore(object):
    '''Implements the data storage model on a MySQL database'''


    def __init__(self, db_info_dict):
        '''Opens a connection to the mySQL database'''
        self.db_info = db_info_dict
        self.mysql_api = mysql.connector.connect(**self.db_info)

    def load_network_topogoly(self):
        '''Gets the network topology from the database'''
        pass
