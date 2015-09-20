'''
Created on Sep 20, 2015

@author: mcasadevall
'''
import unittest
from dynipd.config_parser import ConfigurationParser
import sys
import configparser
from dynipd.mysql_datastore import MySQLDataStore


class TestDatastore(unittest.TestCase):


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

    def tearDown(self):
        pass


    def testName(self):
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
