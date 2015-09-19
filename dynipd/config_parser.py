'''
Created on Sep 18, 2015

@author: mcasadevall
'''

import configparser

class ConfigurationParser(object):
    '''Configuration File Helper'''

    def __init__(self, configuration_file):
        '''Loads the configuration file and initializes config praser'''
        self.config_parser = configparser.SafeConfigParser()

        with open(configuration_file, 'r') as file:
            self.config_parser.readfp(file)

        self._db_config = {}
        self._load_database_configuration()

    def _load_database_configuration(self):
        '''Loads the database API from the config file'''
        self._db_config['host'] = self.config_parser.get("dynipd-database", "host")
        self._db_config['user'] = self.config_parser.get("dynipd-database", "user")
        self._db_config['password'] = self.config_parser.get("dynipd-database", "password")
        self._db_config['database'] = self.config_parser.get("dynipd-database", "database")


    def get_database_configuration(self):
        '''Returns database configuration'''
        return self._db_config

    def get_node_configuration(self):
        '''Gets information related to this node'''
        pass
