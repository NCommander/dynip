'''
Created on Sep 20, 2015

@author: mcasadevall
'''
import unittest
from dynipd.config_parser import ConfigurationParser
import sys
import configparser
from dynipd.server.machine import Machine
from dynipd.mysql_datastore import MySQLDataStore
from socket import AF_INET, AF_INET6


class TestDatastore(unittest.TestCase):
    '''Loads up the data store with example data (which is reset through setUp) for each test

    Because NetworkBlock and Allocation are highly connected to the datastore, they get tested
    through this test file as well'''

    def setUp(self):
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
        self.datastore = MySQLDataStore(cfg_file.get_database_configuration('dynipd-test'))
        self.datastore.load_file_into_database('sql/schema.sql')

        self.datastore.create_machine('TestMachine', 'sometoken')
        self.datastore.create_machine('TestMachine2', 'sometoken')
        self.datastore.create_machine('TestMachine3', 'sometoken')
        self.datastore.create_network('Minecraft:LOC', 'TestNet', AF_INET, '10.0.2.0/24', 32, '')
        self.datastore.create_network('Minecraft:LOC2', 'TestNet', AF_INET, '10.0.3.0/24', 32, '')
        #self.datastore.create_network('Minecraft:LOCv6', 'TestNet', AF_INET6, 'fd00:a3b1:78a2::/48',
        #                               64, '')

    def tearDown(self):
        pass

    def testBlockAllocations(self):
        '''Tests that blocks can be allocated to machines, and IP statuses set'''

        # NOTE: this relays on the behavior of MySQL AUTO_INCREMENT to predict IDs

        # Test the machine class here
        machine = Machine('TestMachine', self.datastore)
        self.assertEquals(machine.get_id(), 1)
        self.assertEquals(machine.get_name(), 'TestMachine')

        machine = Machine('TestMachine3', self.datastore)
        self.assertEquals(machine.get_id(), 3)
        self.assertEquals(machine.get_name(), 'TestMachine3')

        machine = Machine('TestMachine2', self.datastore)
        self.assertEquals(machine.get_id(), 2)
        self.assertEquals(machine.get_name(), 'TestMachine2')

        machine = Machine('TestMachine', self.datastore)
        networks = self.datastore.get_networks()
        network = networks.pop()
        allocation = network.create_new_allocation(machine)
        unusued_ip = allocation.get_unused_ip()
        allocation.mark_ip_as_reserved(unusued_ip)
        allocation.mark_ip_as_reserved(unusued_ip)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
