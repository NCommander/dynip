'''
Created on Sep 24, 2015

@author: mcasadevall
'''
import unittest

import sys
import configparser
from socket import AF_INET, AF_INET6
from dynipd.mysql_datastore import MySQLDataStore
from dynipd.config_parser import ConfigurationParser
from dynipd.network_block import NetworkBlock
from dynipd.server.allocation import AllocationServerSide

class TestNetworkBlock(unittest.TestCase):


    @classmethod
    def setUpClass(cls):
        '''Load test database configuration'''
        # Make sure our config file is kosher
        cfg_file = None
        try:
            cfg_file = ConfigurationParser('dynipd-test.ini')
        except FileNotFoundError:
            sys.stderr.write(("Configuration file not found. Bailing out!\n"))
            sys.exit(-1)
        except configparser.MissingSectionHeaderError:
            sys.stderr.write("Configuration stanza is missing. Bailing out!\n")
            sys.exit(-1)

        # Initialize our data store; on initialization, it will pull
        # configuration settings like network topology
        cls.datastore = MySQLDataStore(cfg_file.get_database_configuration('dynipd-test'))
        cls.datastore.load_file_into_database('sql/schema.sql')

        cls.datastore.create_machine('TestMachine', 'sometoken')
        cls.datastore.create_machine('TestMachine2', 'sometoken')
        cls.datastore.create_machine('TestMachine3', 'sometoken')
        cls.datastore.create_network('LOC', 'TestNet', AF_INET, '10.0.2.0/24', 32, '')
        cls.datastore.create_network('LOC2', 'TestNet', AF_INET, '10.0.3.0/24', 32, '')
        cls.datastore.create_network('LOCv6', 'TestNet', AF_INET6, 'fd00:a3b1:78a2::/48',
                                       64, '')

    def test_equal_comparsion(self):
        '''Tests if a network block equals itself successfully'''
        datastore = self.__class__.datastore
        network1 = datastore.get_network_by_name('LOC')
        network2 = datastore.get_network_by_name('LOC')

        self.assertEqual((network1 == network2), True, "Same network does not equal each other")

    def test_not_equal_comparsion(self):
        '''Tests if two differents network block don't equal themselves successfully'''
        datastore = self.__class__.datastore
        network1 = datastore.get_network_by_name('LOC')
        network2 = datastore.get_network_by_name('LOC2')

        self.assertEqual((network1 == network2), False, "Same network does not equal each other")

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
