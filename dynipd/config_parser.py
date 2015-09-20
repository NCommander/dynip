'''
Created on Sep 18, 2015

@author: mcasadevall
'''

import configparser

class ConfigurationParser(object):
    '''Configuration File Helper'''

    def __init__(self, configuration_file):
        '''Loads the configuration file and initializes config praser'''
        self.config_parser = configparser.ConfigParser()

        with open(configuration_file, 'r') as file:
            self.config_parser.read_file(file)

    def _load_database_configuration(self, config_stanza='dynipd-database'):
        '''Loads the database API from the config file'''
        db_config = {}
        db_config['host'] = self.config_parser.get(config_stanza, "host")
        db_config['user'] = self.config_parser.get(config_stanza, "user")
        db_config['password'] = self.config_parser.get(config_stanza, "password")
        db_config['database'] = self.config_parser.get(config_stanza, "database")

        return db_config

    def get_database_configuration(self, config_stanza='dynipd-database'):
        '''Returns database configuration'''
        return self._load_database_configuration(config_stanza)

    def get_node_configuration(self):
        '''Gets information related to this node'''
        pass
