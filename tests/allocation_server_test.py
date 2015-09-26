# pylint: disable=invalid-name

'''
Created on Sep 20, 2015

@author: mcasadevall
'''
import unittest
import sys
import configparser

from socket import AF_INET, AF_INET6
from dynipd.server.machine import Machine
from dynipd.mysql_datastore import MySQLDataStore
from dynipd.config_parser import ConfigurationParser
from dynipd.server.allocation import AllocationServerSide

class AllocationServerSideTest(unittest.TestCase):
    '''Tests the AllocationServerSide class'''

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


    def test_create_and_delete_ipv4_allocations(self):
        '''Creates a basic IPv4 allocation'''
        datastore = self.__class__.datastore

        # First, get our machine and create an allocation
        machine = Machine('TestMachine', self.datastore)
        ipv4_network = datastore.get_network_by_name('LOC')
        allocation = ipv4_network.create_new_allocation(machine)

        # NetworkBlock should assign us 10.0.2.1/32
        self.assertEquals(allocation.get_allocation_cidr(), '10.0.2.1/32', 'Did not get 10.0.2.1')

        # Check that the machine and NetworkBlock objects have our list
        machine_allocations = machine.list_allocations()
        if not allocation in machine_allocations:
            self.fail ("Allocation not found in list_allocations")

        #unusued_ip = allocation.get_unused_ip()
        #allocation.mark_ip_as_reserved(unusued_ip)

        # Now try to remove it
        allocation.remove()

        # Confirm that the allocations are removed from the NetworkBlock

    def test_create_and_delete_ipv6_allocation(self):
        '''Create a basic IPv6 allocation'''
        datastore = self.__class__.datastore

        # First, get our machine and create an allocation
        machine = Machine('TestMachine', self.datastore)
        ipv6_network = datastore.get_network_by_name('LOCv6')
        allocation = ipv6_network.create_new_allocation(machine)

        # NetworkBlock should assign us fd00:a3b1:78a2:1::/64
        self.assertEquals(allocation.get_allocation_cidr(),
                          'fd00:a3b1:78a2:1::/64',
                          'Did not get fd00:a3b1:78a2:1::/64')

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
